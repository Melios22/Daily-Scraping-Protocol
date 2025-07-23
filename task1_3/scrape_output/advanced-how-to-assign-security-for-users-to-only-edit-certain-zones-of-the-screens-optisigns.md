---
url: https://support.optisigns.com/hc/en-us/articles/1500002047642-Advanced-How-to-assign-security-for-users-to-only-edit-certain-zones-of-the-screens
date_scraped: [2025-07-23 13:54:43]
---

Skip to main content
[ ![OptiSigns Help Center home page](/hc/theming_assets/01HZKNYSEQ6GRC01C0J27PZ3RC) ](/hc/en-us "Home")
__
[ ![OptiSigns Help Center home page](/hc/theming_assets/01HZKNYSEQ6GRC01C0J27PZ3RC) ](/hc/en-us "Home")
#  Advanced: How to assign security for users to only edit certain zones of the screens 
This article will guide you through how to assign security for users to only edit certain zones of the screens.  
Use Case: a Company with 2 departments, Department A and Department B, each will have a section/zone of the screen that they can update freely, but they cannot change the zone belong to other departments. Administrators can edit modify the whole screen.
[![](/hc/article_attachments/360102952113)](/hc/article_attachments/360102952113)
To do this we will need to:
1) You need to add the users to the Account Member. Please set them as a User. Here is a related [article](https://support.optisigns.com/hc/en-us/articles/360016990233-Multi-users-Invite-your-team-members-to-your-account).
[![](/hc/article_attachments/360102942833)](/hc/article_attachments/360102942833)
2) Create Files/Assets folders for Department A & Department B
[![](/hc/article_attachments/360100781194)](/hc/article_attachments/360100781194)
3) Create 2 playlists: Department A & Department B
[![](/hc/article_attachments/360102942173)](/hc/article_attachments/360102942173)
4) Create a SplitScreen & Assign playlist
[![](/hc/article_attachments/1500001932161)](/hc/article_attachments/1500001932161)
5) Set up security for Screens, Files/Assets, Playlist folders
For the screen: You can edit the "Change Permission" in the folder. You can set **Admin Only**.
Put your screens in this folder so only Admins can edit & change assignment for the screens.
[![](/hc/article_attachments/1500001932181)](/hc/article_attachments/1500001932181)
[![](/hc/article_attachments/360100781154)](/hc/article_attachments/360100781154)
For the Department A folder in Files/Assets: You can edit the "Change Permission" in the folder. You can set it to **DepartmentA User**.
[![](/hc/article_attachments/360102941973)](/hc/article_attachments/360102941973)
For the Department B folder in Files/Assets: You can edit the "Change Permission" in the folder. You can set it to **DepartmentB User**.
[![](/hc/article_attachments/1500001932301)](/hc/article_attachments/1500001932301)
For the Department A Playlist folder in Playlist: You can edit the "Change Permission" in the folder. You can set it to **DepartmentA User**.
[![](/hc/article_attachments/1500001932661)](/hc/article_attachments/1500001932661)
For the Department B Playlist folder in Playlist: You can edit the "Change Permission" in the folder. You can set it to **DepartmentB User**.
[![](/hc/article_attachments/1500001932781)](/hc/article_attachments/1500001932781)
Now we have:   
Admin can see:
  * Administration folder in the Screen.
  * Department A and Department B folder in the Files/Assets
  * Department A and Department B folder in the Playlist


DepartmentA User can see the
  * Department A folder in the Files/Assets
  * Department A Playlist Folder in the Playlist 


DepartmentB User can see the
  * Department B folder in the Files/Assets
  * Department B Playlist Folder in the Playlist 


If you have any additional questions, concerns or any feedback about OptiSigns, feel free to reach out to our support team at [support@optisigns.com](mailto:support@optisigns.com)
