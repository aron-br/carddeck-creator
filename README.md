# carddeck-creator
Create a custom version of a song guessing game based on a Spotify playlist


# Usage
First create a spotify app and add the client ID and client secret to your environment
```
touch ~/.bash_profile
open -a TextEdit.app ~/.bash_profile
```
add these lines to the file, while replacing <> with your ID and secret, and save the edited file
```
export SPOTIPY_CLIENT_ID=<YOUR-CLIENT-ID>
export SPOTIPY_CLIENT_SECRET=<YOUR-CLIENT-SECRET>
```
Lastly, update your environment and check that the variables are set correctly
```
source ~/.bash_profile
echo $SPOTIPY_CLIENT_ID
echo $SPOTIPY_CLIENT_SECRET
```

Update the path to the styles.css file in the .jinja template
```
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <link rel="stylesheet" type="text/css" href="<ABSOLUTE-PATH-TO>/styles.css">
</head>
```
