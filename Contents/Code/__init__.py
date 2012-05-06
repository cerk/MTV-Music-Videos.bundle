import re, string, datetime

MTV_PLUGIN_PREFIX   = "/video/MTV"
MTV_ROOT            = "http://www.mtv.com"
MTV_VIDEO_PICKS     = "http://www.mtv.com/music/videos"
MTV_VIDEO_PREMIERES = "http://www.mtv.com/music/videos/premieres"
MTV_VIDEO_TOPRATED  = "http://www.mtv.com/music/video/popular.jhtml"
MTV_VIDEO_YEARBOOK  = "http://www.mtv.com/music/yearbook/"
MTV_VIDEO_DIRECTORY = "http://www.mtv.com/music/video/browse.jhtml?chars=%s"

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.162 Safari/535.19'

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(MTV_PLUGIN_PREFIX, MainMenu, "MTV Music Videos", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.art = R('art-default.jpg')
  MediaContainer.title1 = 'Top Picks'
  DirectoryItem.thumb=R("icon-default.png")

  HTTP.Headers['User-Agent'] = USER_AGENT
  HTTP.CacheTime=3600

def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R("icon-default.png"))
  
####################################################################################################
def MainMenu():
    dir = MediaContainer(mediaType='video') 
    dir.Append(Function(DirectoryItem(VideoPage, "Top Picks"), pageUrl = MTV_VIDEO_PICKS))
    dir.Append(Function(DirectoryItem(VideoPage, "Premieres"), pageUrl = MTV_VIDEO_PREMIERES))
    dir.Append(Function(DirectoryItem(VideoPage, "Most Popular"), pageUrl = MTV_VIDEO_TOPRATED))
    dir.Append(Function(DirectoryItem(ArtistAlphabet, "Artists")))
    dir.Append(Function(DirectoryItem(Yearbook, "Yearbook")))
    return dir

####################################################################################################
def VideoPage(sender, pageUrl):
    dir = MediaContainer(title2=sender.itemTitle)
    Log("Scraping "+pageUrl)
    content = HTML.ElementFromURL(pageUrl)
    for item in content.xpath('//div[@class="title2"]'):
        link = MTV_ROOT + item.xpath("a")[0].get('href')
        image = ''
        xpathImg = item.xpath("a/img")
        if len(xpathImg) > 0:
            image = xpathImg[0].get('src')
        title = ''
        title = item.xpath("a")[-1].text.strip()
        if title == None or len(title) == 0:
            if len(xpathImg) > 0:
                title = xpathImg[-1].get('alt')
        if title == None or len(title) == 0:
            title = item.xpath("a/meta")[0].get('content')
        title = title.replace('"','')
        dir.Append(Function(VideoItem(FindEpisodePlayer, title=title, thumb=Function(Thumb,url=image)), url=link))
    if len(dir)==0:
      return MessageContainer("Sorry !","No video available in this category.")
    else:
      return dir
    
####################################################################################################
def Yearbook(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for year in HTML.ElementFromURL(MTV_VIDEO_YEARBOOK).xpath("//div[@class='group-a']/ul/li/a"):
        link = MTV_ROOT + year.get('href')
        title = year.text.replace(' Videos of ','')
        dir.Append(Function(DirectoryItem(YearPage, title), pageUrl = link))
    return dir
    
####################################################################################################
def YearPage(sender, pageUrl):
    dir = MediaContainer(title2=sender.itemTitle)
    for video in HTML.ElementFromURL(pageUrl).xpath("//div[@class='mdl']//ol/li"):
        url = MTV_ROOT + video.xpath('.//a')[0].get('href')
        img = video.xpath('.//a/img')[0]
        title = img.get('alt')
        if title != None:
            title = title.strip('"').replace('- "','- ').replace(' "',' - ')
            thumb = MTV_ROOT + img.get('src')
            link = re.sub('#.*','', url)
            dir.Append(WebVideoItem(link, title=title, thumb=Function(Thumb,url=thumb)))
    return dir

####################################################################################################
def ArtistAlphabet(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for ch in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ#'):
        dir.Append(Function(DirectoryItem(Artists, ch), ch = ch))
    return dir

####################################################################################################
def Artists(sender, ch):
    dir = MediaContainer(title2=sender.itemTitle)
    url = MTV_VIDEO_DIRECTORY % ch
    for artist in HTML.ElementFromURL(url).xpath("//ol/li//a"):
        url = MTV_ROOT + artist.get('href')
        title = artist.text
        dir.Append(Function(DirectoryItem(VideoPage, title), pageUrl = url))
    if len(dir)==0:
      return MessageContainer("Error","No artist in this category")
    else:
      return dir
      
####################################################################################################
def FindEpisodePlayer(sender, url):
    content = HTTP.Request(url).content
    flashlink = ''
    if content.find('MTVN.Player.isVevoVideo = true;') >= 0:
        # Vevo video
        flashlink = re.search('MTVN.Player.vevoVideoId = "(?P<id>.+)"', content).group('id')
        flashlink = 'http://videoplayer.vevo.com/embed/standardv3/3?playerType=standard&videoId=' + flashlink + '&autoplay=1'
        Log('FlashLink:'+flashlink)
        return Redirect(WebVideoItem(flashlink))
    else:
        # MTV video
        flashlink = re.search('http://media.mtvnservices.com/(?P<id>.+video[^"]+)', content).group('id')
        flashlink = 'http://media.mtvnservices.com/player/prime/mediaplayerprime.1.12.1.swf?uri=' + flashlink
        Log('FlashLink:'+flashlink)
        return Redirect(WebVideoItem(flashlink))
