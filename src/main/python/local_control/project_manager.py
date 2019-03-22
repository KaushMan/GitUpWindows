import os
import git
from git import Repo
from git import IndexFile
from multiprocessing import Process
import sys
sys.path.append(os.path.normpath(os.path.join(os.path.realpath(__file__), "..", "..")))
from github_control import user_account as uc
from daemon import csv_editor as CSV
from daemon_launcher import daemon_launcher as DMN

class ProjectManager(object):


    def __init__(self, user: uc.UserAccount):
        """
        Construct a new ProjectManager instance to view projects, must be associated with 
        a UserAccount
        """
        self.curr_user = user
        return None

    def find_project_repo(self, path: str) -> Repo: 
        """
        Arguments:
            path: the absolute path of the directory to be checked.
        
        Returns Repo object if the directory given from path is a working tree directory for 
        a repository or a subdirectory of a working tree, returns None otherwise. 
        """
        norm_path = os.path.normpath(path)
        if os.path.exists(norm_path) is False:
            raise ValueError("Path given to find a repository is not a valid file path.")
        else:
            try:
                return Repo(path, search_parent_directories=True)
            except:
                return None
        
    def view_project_repo(self, path: str):
        """
        Arguments:
            path: the absolute path of the directory to be checked, error if path is invalid.
        
        If the absolute path is an existing working tree directory or a subdirectory then
        GitUp recognizes this as a project and ensures a remote repository is associated
        with the user's account to backup the local repository. If the given path is not 
        part of an existing repository then a new repository is created and associated with
        a remote repository on the user's account. Always returns a Repo instance associated
        with the path.
        """
        norm_path = os.path.normpath(path)
        if os.path.exists(norm_path) is False:
            raise ValueError("Path given to view a project is not a valid file path.")

        # check if directory is associated with an existing repository
        repo = self.find_project_repo(norm_path)

        if repo is None:
            # if the directory is not part of an existing repository then create a new one associated with
            # a remote on the user's GitHub account.
            # CREATE A NEW REPOSITORY
            repo = Repo.init(path=norm_path)
            repo.git.init()
        # ensure the repository has the origin remote
        try:
            repo.remote(name="origin")
        except ValueError:
            self.curr_user.create_remote_repo(repo)
        # TODO: update the .csv file and restart the daemon
        self.__update_daemon_csv(norm_path)
        # return the Repo object for this path
        return repo    

    def restore_project_repo(self, path: str, repo_name: str):
        """
        Arguments:
            path: the absolute path of the directory to restore the repository, error if path is invalid.
            repo_name: the name of the repository as shown on GitHub, error if the current user does not
                have a repo associated with this name.
        Restores the latest version of a project on a remote repository (associated with the user's GitHub
        account) to a folder created using the repo_name at the given path. Returns the repository object if 
        restored properly, otherwise returns None.
        """
        norm_path = os.path.normpath(path)
        if os.path.exists(norm_path) is False:
            raise ValueError("Path given to restore a project is not a valid file path.")

        # check if the directory is associated with an existing repository
        repo = self.find_project_repo(norm_path)

        if not repo is None:
            raise ValueError("Path provided to an existing project.")

        # check if the repo_name exsits on the users account
        existing_repos = self.curr_user.get_remote_repos()
        found_repo = None
        for r in existing_repos:
            if r[0] == repo_name:
                found_repo = r

        # clone the repo to the path
        if found_repo is None:
            raise ValueError("No existing project repository with repo_name for this user's account.")
        
        # join norm path with repo_name for new directory
        norm_path = os.path.join(norm_path, repo_name)
        # perform an authenticated clone
        cloned_repo = git.Repo.clone_from(self.curr_user.create_clone_url(found_repo[1]), norm_path, branch='master')
        try:
            # recreate the origin remote to avoid storing token
            cloned_repo.delete_remote(cloned_repo.remote())
            cloned_repo.create_remote(name="origin", url=found_repo[1]) 
            cloned_repo.remote()
            self.__update_daemon_csv(norm_path) 
        except:
            raise sys.stderr.write("Cloned repository does not have an origin remote. GitUp will not track automatically.\n")
        return cloned_repo

    def __start_or_restart_daemon(self):
        if DMN.daemon_is_running():
            DMN.restart_daemon()
        else:
            DMN.start_daemon()
    
    def __update_daemon_csv(self, path: str) -> bool:
        """
        Arguments:
            path: the absolute path of the project to add to the CSV tracked by the Daemon.
        
        Adds the path specified by the argument to the CSV tracked by the Daemon and restart
        it. Returns True if the path was successfully added, returns False if the path was 
        already in the CSV. Creates a new project CSV at the CSV path if it doesn't exist. 
        Error if path is not a valid directory.
        """
        norm_path = os.path.normpath(path)
        if os.path.exists(norm_path) is False:
            raise ValueError("Path given to project to CSV is not a valid file path.")
        try:
            CSV.add_project(path)
        except ValueError:
            return False
        # if necessarry then restart the Daemon
        # Not using a process causes a fairly complicated bug, due to
        # the double fork attempting to call exit from the parent processes. To
        # avoid this restarting the daemon should be done from a separate process.
        p = Process(target=self.__start_or_restart_daemon)
        p.start()
        p.join()
        return True

    def __remove_daemon_csv(self, path: str) -> bool:
        """
        Arguments:
            path: the absolute path of the project to remove from the CSV tracked by the Daemon.
        
        Removes the path specified by the argument to the CSV tracked by the Daemon and restart
        it. Returns True if the path was successfully removed, returns False if the path was 
        not already in the CSV or CSV doesn't exist.
        """
        try:
            CSV.remove_project(path)
        except Exception:
            return False
        # if necessarry then restart the Daemon
        # Not using a process causes a fairly complicated bug, due to
        # the double fork attempting to call exit from the parent processes. To
        # avoid this restarting the daemon should be done from a separate process.
        p = Process(target=self.__start_or_restart_daemon)
        p.start()
        p.join()
        return True
    
    def view_repo_commits(self, path: str):
        """
        Arguments:
            path: the absolute path of the directory to be checked, error if path is invalid.
        Returns a List of commit objects for the repo at the given path.
        """
        curr_repo = self.find_project_repo(path)
        return curr_repo.iter_commits()
    
    def revert(self, file_path: str, commit: git.Commit):
        """
        Arguments:
            path: the absolute path of the file to be reset, must be part of a repo, 
            error if path is invalid.
            commit: the Commit object to reset this file to.
        Resets the file given at path to the given state described by the Commit object.
        """
        norm_path = os.path.normpath(file_path)
        if os.path.exists(norm_path) is False:
            raise ValueError("Path given to file to reset is not a valid file path.")
        
        # get the repo
        curr_repo = self.find_project_repo(norm_path)
        # instantiate the index
        curr_index = git.IndexFile(curr_repo, norm_path)
        curr_index.reset(commit=commit, paths=[norm_path])
    
    def stop_tracking_project(self, path: str):
        """
        Arguments:
            path:

        Removes the given path from the list of projects being tracked.
        Throw a ValueError if the path is not being tracked.
        """
        if not self.__remove_daemon_csv(path):
            raise ValueError("The provided path {} is not being tracked by GitUp.".format(path))
    
    def delete_project_repo(self, path: str, remove_files=False):
        """
        Arguments:
            path: the absolute path of a working tree directory of an existing local repository, error if no repo.
            remove_files: if True remove the repository files on the user's GitHub acccount.
        
        Removes the origin remote from a local repository and alerts the project directory from those
        being tracked by GitUp. Deletes the repository files on the users
        GitHub account if remove_files is True. Returns True if repository successfully removed,
        returns False if the repository was not removed.
        """
        # check if the path is valid
            # if the path is not valid then throw an error
        # check if the directory is associated with an existing repository
            # if the directory is not associated with an existing repository then throw an error
        # get the name of the repository
        # remove the origin remote from the local repository
        # check that the repository name exists on the user's GitHub account
        # if remove_files is True then remove_files from GitHub
        # TODO: update the csv file and restart the daemon
        raise NotImplementedError()