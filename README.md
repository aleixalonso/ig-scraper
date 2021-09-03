# ig-scraper

- install selenium dependency: pip3 install selenium, use python3
- download selenium chromedriver, with the unzipped file: mv ~/Downloads/chromedriver /usr/local/bin
- install the google translate dependency, pip3 install googletrans
- install scrubadub for text anonymization pip3 install scrubadub and python3 -m textblob.download_corpora
- pip3 install requests
- interactive shell: python3 -i main.py
- in the file options.py, introduce your credentials (if you want to use the method logIn(), if not, you can ignore that)
- in the options.py file you can save links arrays in order to performe a test for scrapping, if you want to save those arrays, you can call from the interactive shell this line: print(bot.getLinksFromExplora("hashtagtoexplore", numberoflinks))
- the getHastagPhotos() will perform link collection and scrapping, so you only have to call bot.getHastagPhotos("hashtagtoexplore", numberoflinks) from the interactive shell
- never git add the options.py file
- be sure two factor authentication is not enable
