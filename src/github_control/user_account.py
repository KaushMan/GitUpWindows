import os
from github import Github
from git import Repo
from git import IndexFile

class UserAccount(object):
    """
    This class manages information about the currently logged in user (and their remote repositories)
    for interacting with the UI and Daemon.
    """

    def __init__(self, user_name: str, password: str):
        """
        Arguments:
            user_name: user name for a GitHub account, assumes valid.
            password: password for a GitHub account, assumes valid.
        Logs in to a user account and creates a token for GitUp that
        will be stored with the scope of "all" at the path /tmp/GitUp/token.txt.
        If a token for GitUp already exists than an error will be thrown.
        """
        self.github_control = Github(login_or_token=user_name, password=password)

        # create a new token

        # write the token at the default path
            # throw error if already exists

    @staticmethod 
    def login_to_existing_user(self, token_file_path: str=None):
        """
        Arguments:
            token_file_path: opens the given at this path and reads the first line for an authorization token.

        If a token_file_path is provided then checks the file given at path for an authorization
        token, if none then throw ValueError. Otherwise searches default path /tmp/GitUp/token.txt
        for token. If neither exist then throws a ValueError. After a token has been found,
        validates this token and attempts to create a Github controller. If creation fails then throw
        a value error, if succeeds then return a UserAccount object.
        """
        if not token_file_path:
            token_file_path = os.path.normpath("/tmp/GitUp/token.txt")
        
        norm_path = os.path.normpath(token_file_path)
        if os.path.exists(norm_path) is False:
            raise ValueError("Path given to find a repository is not a valid file path.")

        # get the token from the file and read the first line

        # create a github control with the token

        return NotImplementedError()

    def get_name(self):
        """
        Returns the name associated with this user account.
        """
        return self.github_control.get_user().name
    
    def get_id(self):
        """
        Returns the user (screen) id associated with this user account.
        """
        return self.github_control.get_user().id
    
    def get_profile_url(self):
        """
        Returns the profile URL for the current user
        """
        return self.github_control.get_user().html_url

    def get_profile_image_url(self):
        """
        Returns the profile image URL for the current user
        """
        return self.github_control.get_user().avatar_url


    def github_controller(self):
        """
        Returns the GitHub controller for this user (allows pushing & pulling from Repository)
        """
        return self.github_control
    
    def get_remote_repos(self):
        """
        Returns a list of tuples in the form: 
        (repo_name, repo_clone_url)
        representing the name's and clone urls of the current user's remote repositories.
        """
        repos = list()
        for repo in self.github_control.get_user().get_repos():
            repos.append(tuple([repo.name, repo.clone_url]))
        return repos

    def create_remote_repo(self, local_repo: Repo):
        """
        Arguments:
            local_repo: GitPython Repo object to create a remote repository on the user account.

        Creates a remote repository under the last directory of the working_tree_dir
        and add remote under the name "GitUp" to this local repository on the current user's
        GitHub account. Pushes all contents of local repo into remote repo after creation.
        If local_repo is not a GitPython Repo throw error.
        If a "GitUp" remote already exists throw an error.
        If push fails after a remote repo is created then throw an error.
        """
        # verify that there is not a GitUp remote
        try:
            local_repo.remote(name="GitUp")
            raise AssertionError("local_repo already has a GitUp remote.")
        except ValueError:
            # create the remote repository
            repo_name = os.path.basename(os.path.normpath(local_repo.working_tree_dir))
            self.github_control.get_user().create_repo(name=repo_name, description=str("Repository managed by GitUp."))

            # ERROR CHECK NEEDED
            # add the remote from the remote repository to the local repository
            local_repo.create_remote(name="GitUp", url=self.github_control.get_repo(repo_name).url)

            # create index for this repo
            curr_index = IndexFile(local_repo)
            
            # add all changes
            curr_index.add(".")

            # commit 
            curr_index.commit("Added all changes after creating remote repo.")

            # push to the remote
            if local_repo.remote(name="GitUp").push() is None:
                raise AssertionError("Push to origin failed after remote repo created for {1}".format(local_repo.working_tree_dir))
    
    def push_to_remote(self, local_repo):
        """
        Argument:
           local_repo: GitPython repo to push to changes to remote.
        
        Pushes the latest changes to the remote repository under remote "origin".
        If local_repo is not a GitPython Repo throw error.
        If local_repo does not have a remote named "origin" throw error. 
        If push to remote "origin" fails throw error.
        """
        # verify this repo has a GitUp remote
        try:
            local_repo.remote(name="GitUp")
        except ValueError:
            raise AssertionError("No GitUp remote for repo {1}.".format(local_repo.working_tree_dir))
        # push to the remote
        if local_repo.remote(name="GitUp").push() is None:
            AssertionError("Push to GitUp remote failed for repo {1}.".format(local_repo.working_tree_dir))

    def pull_to_local(self, local_repo: Repo):
        """
        Argument:
            local_repo: GitPython repo to pull latest changes from the origin remote

        Pulls the latest changes to this local repository from the remote "origin".
        If local_repo is not a GitPython Repo throw error.
        If local_repo does not have a remote named "origin" throw error. 
        If pull from remote "origin" fails throw error.
        """
        try:
            local_repo.remote(name="GitUp")
        except ValueError:
            raise AssertionError("No GitUp remote for repo {1}.".format(local_repo.working_tree_dir))
        # push to the remote
        if local_repo.remote(name="GitUp").pull() is None:
            AssertionError("Pull to repo {1} from remote GitUp failed.".format(local_repo.working_tree_dir))