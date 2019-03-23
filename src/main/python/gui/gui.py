import sys
import os
import csv
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import git
from git import Repo
from git import Commit
import time
from gui import commit_grouper as grouper
from gui.lib import Tooltip
sys.path.append(os.path.normpath(os.path.join(os.path.realpath('__file__'), "..", "..")))
from local_control import project_manager
from github_control import user_account
from daemon import repository

# Represents the GitHub credentials of the current user
user = None

# Object that facilitates interaction between the user and Git repositories
proj_manager = None

# Represents the absolute path to the Git repository the user is interacting with
proj_dir = None

# Represents the absolute file path of a file being viewed
filepath = None

# Represents the current Git repository the user is interacting with
repo = None

# Main Application
class GitUpApp(tk.Tk):
    
    #Initialization of App
    def __init__(self):

        #Initial configuration
        tk.Tk.__init__(self)
        self.geometry('600x350')
        self.title('GitUp')
        self._frame = None
        global user

        #Checks if there is a currently logged in user   
        try:
            # There is a logged in user. Sets up user account and goes to main menu
            user = user_account.UserAccount("/tmp/gitup/token.txt")
            self.switch_frame(StartingMenu)

        except ValueError:
            #There isn't a currently logged in user. Goes to login menu to get one.
            self.switch_frame(LoginWindow)

    '''
    Helper method that allows the application to switch frames.
    frame_class: the frame class that the app is switching to
    Destroys the old frame, if it exists, and switches to frame_class
    '''
    def switch_frame(self, frame_class):
        # Checks if there is an existing frame
        if self._frame is not None:
            # Destroys frame if it exists
            self._frame.destroy()

        self._frame = frame_class(self)
        self._frame.pack(expand = 1)

# Starting Menu that greets the user once they are logged in
class StartingMenu(tk.Frame):

    # Window initialization
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        global user
        global proj_manager

        frame = tk.Frame(master)

        # Text in Starting Menu
        tk.Label(self, text = "GitUp").pack(fill_='x')
        tk.Label (self, text = "v1.0.0").pack(fill_='x')
        tk.Label(self, text = "Welcome " + user.get_login() + "!").pack(fill_='x')
        
        '''
        Login button removed for now (we don't want multiple users using the same system)
        # Button to logout the user and prompt them to log in
        tk.Button(self, text = "Logout",
                command = lambda: master.switch_frame(LoginWindow)).pack()
        '''
        # Button to open menu for viewing a project and adding it to GitUp's
        # tracked projects if it is not already being tracked
        self.backup = tk.Button(self, text = "Backup New Project",
                command = lambda: self.backup_project())
        self.backup.pack(fill_='x')

        backup_ttp_msg = ("Click here if you want to backup a project you're "
                "working on in this machine with GitUp!")
        backup_ttp = Tooltip.CreateToolTip(self.backup, backup_ttp_msg)

        # Button to open menu for adding a remote project to local machine
        self.restore = tk.Button(self, text = "Restore Backed up Project",
            command = lambda: master.switch_frame(ExistingProjects))
        self.restore.pack(fill_='x')

        restore_ttp_msg = ("Click here if you want to add a project "
                "you've already backed up through GitUp to this "
                "machine to work on!")
        restore_ttp = Tooltip.CreateToolTip(self.restore, restore_ttp_msg)

        # Button to open menu for viewing a project

        self.view = tk.Button(self, text = "View Project",
                command = lambda: master.switch_frame(ViewProjectMenu))
        self.view.pack(fill_='x')

        view_ttp_msg = ("Click here if you want to view the change history "
                "of your project and/or compare, view, and revert to past versions "
                "of specific files!")
        view_ttp = Tooltip.CreateToolTip(self.view, view_ttp_msg)

        # Button to stop tracking project

        self.delete = tk.Button(self, text = "Stop Tracking Project",
                command = lambda: master.switch_frame(DeleteProjectMenu))

        self.delete.pack(fill_='x')

        del_ttp_msg = "Click here if you want GitUp to stop tracking a project!"
        del_ttp = Tooltip.CreateToolTip(self.delete, del_ttp_msg)

        # Sets up the project manager if it isn't already set up
        if proj_manager is None:
            proj_manager = project_manager.ProjectManager(user)
            proj_manager.start_daemon()

    def backup_project(self):
        global proj_dir
        proj_dir = filedialog.askdirectory(initialdir = "/")
        if proj_dir is '':
            return
        global repo
        global proj_manager

        # Check if project is a repo being tracked by GitUp
        try:
            repo = proj_manager.view_project_repo(proj_dir)
        except:
            messagebox.showinfo("Error", "Invalid directory path!")
            
        
# Login window for GitUp
class LoginWindow(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        #Username/password label and text box
        tk.Label(self, text = "Username:").grid(column = 0, row = 0)
        tk.Label(self, text = "Password:").grid(column = 0, row = 1)
        self.username = tk.Entry(self)
        self.username.grid(column = 1, row = 0)
        self.password = tk.Entry(self, show='*')
        self.password.grid(column = 1, row = 1)

        # Button to attempt to login to GitUp
        tk.Button(self, text="Login",
                command = lambda: self.login(master)).grid(row = 2)

    '''
    Logs in to the user's GitHub account with the provided credentials
    master: The main GitUp class. Used to switch frames.
    Attempts to log in to the user's GitHub account with the credentials given
    in the user and password textboxes. If successful, intializes the user and
    creates a token at /tmp/gitup/token.txt for future use. If the login fails,
    does nothing.
    '''
    def login(self, master):
        if self.username.get() != "" and self.password.get != "":
            global user
            try:
                user = user_account.UserAccount(self.username.get(), self.password.get(),
                        "/tmp/gitup/token.txt")
                master.switch_frame(StartingMenu)

            except ValueError:
                messagebox.showinfo("Error", "Username and/or password was incorrect!")

# Window for restoring a remote project to the local machine
class ExistingProjects(tk.Frame):

    # Initializes frame
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text = "Choose a project to restore:").pack()
        global user

        # Create combobox and populate it with all remote projects that be restored
        projs = [i[0] for i in user.get_remote_repos()]
        choose_proj = tk.ttk.Combobox(self, state = "readonly", values = projs)
        choose_proj.pack()

        # Button to add the selected project to the local machine
        tk.Button(self, text = "Add Project",
                command = lambda: self.createFolder(master, choose_proj.get())).pack()

        # Button to go back to the main menu
        tk.Button(self, text = "Back",
                command = lambda: master.switch_frame(StartingMenu)).pack()

    # Creates local version of projName that is synced with the remote version
    def createFolder(self, master, projName):

        if projName is '':
            messagebox.showinfo("Error", "No project selected!")
            return

        # Get directory to create project in
        proj_loc = filedialog.askdirectory(initialdir = "/")
        if proj_loc is '':
            return
        
        # Create the project

        try:
            proj_manager.restore_project_repo(proj_loc, projName)
        except ValueError:
            messagebox.showinfo('Error', ("Can only restore projects in existing directories that "
                    "are not inside a project already being tracked!"))
        master.switch_frame(StartingMenu)

class ViewProjectMenu(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        tk.Label(self, text = "Choose a project to view:").pack()
        global user

        # Create combobox and populate it with all projects that can be viewed
        try:
            with open('/tmp/gitup/repositories.csv') as csvfile:
               readCSV = csv.reader(csvfile, delimiter=',')
               for row in readCSV:
                   projs = [row[0] for row in readCSV]
        except FileNotFoundError:
            projs = []
        choose_proj = tk.ttk.Combobox(self, state = "readonly", values = projs)
        choose_proj.pack()

        # Button to add the selected project to the local machine
        tk.Button(self, text = "View Project",
                command = lambda: self.viewProject(master, choose_proj.get())).pack()

        # Button to go back to the main menu
        tk.Button(self, text = "Back",
                command = lambda: master.switch_frame(StartingMenu)).pack()

    def viewProject(self, master, proj_path):
        global proj_dir
        global repo
        if proj_path is '':
            messagebox.showinfo("Error", "No project selected!")
        else:
            proj_dir = proj_path
            repo = proj_manager.find_project_repo(proj_dir)
            master.switch_frame(ProjectMenu)
        

# Menu for a particular project
class ProjectMenu(tk.Frame):
    
    # Initialize window
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        # Button to compare and revert past versions of a file
        self.view = tk.Button(self, text = "View File",
                command = lambda: self.view_file(master))

        self.view.grid()

        view_ttp_msg = ("Click here to view, compare, and revert to previous versions "
                "of a specific file!")

        view_ttp = Tooltip.CreateToolTip(self.view, view_ttp_msg)

        # Scrollbar for list of grouped commits
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row = 2, column= 1, sticky='ns')
        self.listbox = tk.Listbox(self, yscrollcommand=scrollbar.set)

        # Get all commits for this project
        commitlist = list(repo.iter_commits('--all'))

        # Group the commits by date
        self.commits = grouper.group_commits_by_time(commitlist)

        # Get a sorted list of dates where commits occured
        self.dates = list(self.commits.keys())
        self.dates.sort()

        # Display the dates in sorted order in the listbox
        for date in self.dates:
            self.listbox.insert(tk.END, date)
        scrollbar.config(command=self.listbox.yview)

        commit_description = ("This is an overview of the change history of your project! "
                "Click on a specific date to see a list of all the changes that were "
                "made that day!")

        tk.Message(self, text = commit_description).grid(row=1)
        self.listbox.grid(row=2)


        # Button to go back to the main menu
        tk.Button(self, text = "Back",
                command = lambda: master.switch_frame(StartingMenu)).grid(row=3)

        # Bind double clicking a date to opening a list of all commits on that date
        self.listbox.bind('<Double-1>', lambda x: 
                self.viewDetailedCommits())

    def view_file(self, master):
        global proj_dir
        global filepath

        # Get file to view
        filepath =  filedialog.askopenfilename(initialdir = proj_dir,
                title = "Select file",filetypes = (("text files", "*.txt"),("all files","*.*")))

        if filepath is '':
            return

        if proj_dir not in filepath:
            messagebox.showinfo("Error", "Only files inside the project can be selected")
            return

        master.switch_frame(ViewFile)

    # Displays a popup window that contains a list of all the commits that occured
    # on the date the user specified in the format [Date]-[modified file],[modified file]...
    def viewDetailedCommits(self):
        #Get selected date
        date = self.dates[int(self.listbox.curselection()[0])]
        
        global repo
        commitWindow = tk.Toplevel()
        listbox = tk.Listbox(commitWindow)

        # Get display message for each commit
        commit_messages = []
        for commit in self.commits[date]:
            files = repo.git.show(commit.hexsha, name_only=True, pretty="")
            if not files.startswith('.') and not ('\n.' in files):
                commit_messages.append(str(time.strftime("%a, %d %b %Y %H:%M",
                        time.localtime(commit.committed_date))) + " - " +
                        files.replace('\n', ','))

        # Populate listbox with commit messages
        for date in commit_messages:
            listbox.insert(tk.END, date)

        # Scrollbars for textbox
        xscrollbar = tk.Scrollbar(commitWindow, orient="horizontal")
        xscrollbar.config(command=listbox.xview)
        xscrollbar.pack(side=tk.BOTTOM, fill="x")
        yscrollbar = tk.Scrollbar(commitWindow, orient="vertical")
        yscrollbar.config(command=listbox.yview)
        yscrollbar.pack(side="right", fill="y")
        listbox.pack(side='left', fill='both', expand=True)
        listbox.config(yscrollcommand=yscrollbar.set)
        listbox.config(xscrollcommand=xscrollbar.set)

# Window for comparing and reverting past versions of files
class ViewFile(tk.Frame):

    # Initializes file viewer interface
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        global proj_dir
        global proj_manager
        global filepath

        self.filename = filepath.replace(proj_dir, '')


        buttons = tk.Frame(self)
        # Button to go back to the main menu
        tk.Button(text = "Back",
                command=lambda: master.switch_frame(ProjectMenu)).pack(in_=buttons, side='left')

        # Button to revert the local version of the file to the version selected
        # in the pre combobox
        self.revert = tk.Button(text = "Revert to Old Version",
                command=lambda: self.revertFile(master))

        self.revert.pack(in_=buttons, side = 'left')

        revert_ttp_msg = ("Click here to revert this file back to the version of it "
                "selected in the Old dropdown list!")

        revert_ttp = Tooltip.CreateToolTip(self.revert, revert_ttp_msg)

        # Button to compare the version of the file selected in the pre combobox
        # with the version of the file selected in the post combobox
        self.compare = tk.Button(text = "Compare",
                command = lambda: self.getDiff())
        self.compare.pack(in_=buttons, side = 'left')

        compare_ttp_msg = ("Click here to compare the version of this file selected "
                "in Old with the version selected in New, with additions highlighted in "
                "green and deletions highlighted in red. To just view a past version of "
                "a file, simply select that version in both Old and New!")

        compare_ttp = Tooltip.CreateToolTip(self.compare, compare_ttp_msg)

        buttons.grid()

        # Get list of past versions of the file, store them by the date they were created
        self.commits = list(repo.iter_commits('--all', paths=proj_dir + "/" + self.filename))
        commit_dates = [time.strftime("%a, %d %b %Y %H:%M", time.localtime(commit.committed_date)) 
                for commit in self.commits]

        # Initialize pre and post comboboxes and populate them with the dates of past versions
        # of the file
        version_selection = tk.Frame(self)
        tk.Label(self, text = "Old Version").pack(in_=version_selection, side = 'left')        
        self.pre_version = tk.ttk.Combobox(self, state = "readonly", values = commit_dates)
        self.pre_version.pack(in_=version_selection, side = 'left')
        self.pre_version.current(0)
        tk.Label(self, text="New Version").pack(in_=version_selection, side = 'left')
        self.post_version = tk.ttk.Combobox(self, state = "readonly", values = commit_dates)
        self.post_version.pack(in_=version_selection, side = 'left')
        self.post_version.current(0)
        version_selection.grid(row=1)

        # Configure the textbox to display files and the red/green text for additions and
        # deletions.
        text_frame = tk.Frame(self)
        self.text = tk.Text(text_frame)
        self.text.tag_config("del", background="#fcc9c9", foreground="red")
        self.text.tag_config("add", background="#ccfcc9", foreground="#1e9e16")
        self.text.config(state = tk.DISABLED)

        # Configure scrollbar for the text box
        xscrollbar = tk.Scrollbar(text_frame, orient="horizontal")
        xscrollbar.config(command=self.text.xview)
        xscrollbar.pack(in_=text_frame, side=tk.BOTTOM, fill="x")
        yscrollbar = tk.Scrollbar(text_frame, orient="vertical")
        yscrollbar.config(command=self.text.yview)
        yscrollbar.pack(in_=text_frame, side="right", fill="y")
        self.text.pack(in_ = text_frame, side='left', fill='both', expand=True)
        self.text.config(yscrollcommand=yscrollbar.set)
        self.text.config(xscrollcommand=xscrollbar.set)
        text_frame.grid(row=2, sticky='nsew')

        # Display current version of the file
        self.getDiff()

    '''
    Compares the two versions of the file selected by the user and displays it
    in the textbox. If both versions selected are the same, just displays that version
    of the file.
    '''
    def getDiff(self):       
        global repo
        global proj_dir

        # Clears textbox
        self.text.config(state = tk.NORMAL)
        self.text.delete('1.0', tk.END)

        # Checks if the user selected the same version for pre and post
        if self.pre_version.current() == self.post_version.current():
            # User selected same version for both. Display that version
            file_contents = repo.git.show(self.commits[self.pre_version.current()].hexsha
                    + ":" + self.filename[1:]).splitlines()
            for line in file_contents:
                self.text.insert(tk.END, line + '\n')
        else:
            # User selected different versions. Display the diff between the two versions in
            # the aforementioned format
            diff_contents = repo.git.diff(self.commits[self.pre_version.current()], 
                    self.commits[self.post_version.current()], proj_dir + "/" + self.filename)

            # Checks if both versions of the file are identical
            if diff_contents is '':
                file_contents = repo.git.show(self.commits[self.pre_version.current()].hexsha
                        + ":" + self.filename[1:]).splitlines()
                for line in file_contents:
                    self.text.insert(tk.END, line + '\n')
            diff_lines = diff_contents.splitlines()
            for line in diff_lines[4:]:
                if len(line) > 0 and line[0] == '-':
                    # Line present in old version, but not new
                    self.text.insert(tk.END, line + '\n', 'del')

                elif len(line) > 0 and line[0] == '+':
                    # Line present in new version, but not old
                    self.text.insert(tk.END, line + '\n', 'add')

                # Remove hunk headers from displayed text
                elif len(line) > 0 and line[:2] != '@@':
                    self.text.insert(tk.END, line + '\n')

        # Prevent user from being able to modify contents of the file
        self.text.config(state = tk.DISABLED)

    '''
    Reverts the local copy of the file the user is viewing to the version of the file
    selected by the 'pre' combobox.
    master: The main GitUp class. Used to switch frames.
    '''
    def revertFile(self, master):
        global repo
        global proj_dir
        global project_manager
        global user
        repo.git.checkout(self.commits[self.pre_version.current()].hexsha, '--', self.filename[1:])
        repo.git.add(self.filename[1:])
        repo.git.commit(self.filename[1:], m='Revert')
        user.push_to_remote(repo)
        master.switch_frame(ProjectMenu)
        
# Delete Project Window. Backend not yet implemented
class DeleteProjectMenu(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text = "Choose a project:").pack()
        # Create combobox and populate it with all projects that can be viewed
        try:
            with open('/tmp/gitup/repositories.csv') as csvfile:
               readCSV = csv.reader(csvfile, delimiter=',')
               for row in readCSV:
                   projs = [row[0] for row in readCSV]
        except FileNotFoundError:
            projs = []
        self.choose_proj = tk.ttk.Combobox(self, state = "readonly", values = projs)
        self.choose_proj.pack()
        tk.Button(self, text = "Stop Tracking Project",
                command = lambda: self.delete_project_repo(self.choose_proj.get(), master)).pack()
        tk.Button(self, text = "Back",
                command = lambda: master.switch_frame(StartingMenu)).pack()

    def delete_project_repo(self, path, master):
        global proj_manager
        if path is '':
            messagebox.showinfo("Error", "No project selected!")
        else:
            proj_manager.stop_tracking_project(path)
            proj_manager.start_daemon()
            master.switch_frame(StartingMenu)
            
