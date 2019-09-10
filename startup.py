################################################################################
#      Copyright (C) 2015 Surfacingx                                           #
#                                                                              #
#  This Program is free software; you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation; either version 2, or (at your option)         #
#  any later version.                                                          #
#                                                                              #
#  This Program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with XBMC; see the file COPYING.  If not, write to                    #
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.       #
#  http://www.gnu.org/copyleft/gpl.html                                        #
################################################################################

import xbmc
import xbmcvfs

import glob
import os
import re
import sys

from datetime import timedelta

try:  # Python 3
    from urllib.parse import quote_plus
except ImportError:  # Python 2
    from urllib import quote_plus

from resources.libs.config import CONFIG
from resources.libs import clear
from resources.libs import check
from resources.libs import db
from resources.libs import gui
from resources.libs import logging
from resources.libs import skin
from resources.libs import tools
from resources.libs import update

FAILED = False

########################
#    Check Updates     #
########################


def writeAdvanced():
    if CONFIG.RAM > 1536:
        buffer = '209715200'
    else:
        buffer = '104857600'
    with open(CONFIG.ADVANCED, 'w+') as f:
        f.write('<advancedsettings>\n')
        f.write('	<network>\n')
        f.write('		<buffermode>2</buffermode>\n')
        f.write('		<cachemembuffersize>%s</cachemembuffersize>\n' % buffer)
        f.write('		<readbufferfactor>5</readbufferfactor>\n')
        f.write('		<curlclienttimeout>10</curlclienttimeout>\n')
        f.write('		<curllowspeedtime>10</curllowspeedtime>\n')
        f.write('	</network>\n')
        f.write('</advancedsettings>\n')
    f.close()


while xbmc.Player().isPlayingVideo():
    xbmc.sleep(1000)

### PATH CHECK
logging.log("[Path Check] Started", level=xbmc.LOGNOTICE)
path = os.path.split(CONFIG.ADDON_PATH)
if not CONFIG.ADDON_ID == path[1]:
    gui.DIALOG.ok(CONFIG.ADDONTITLE,
                  '[COLOR {0}]Please make sure that the plugin folder is the same as the addon id.[/COLOR]'.format(CONFIG.COLOR2),
                  '[COLOR {0}]Plugin ID:[/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, CONFIG.ADDON_ID),
                  '[COLOR {0}]Plugin Folder:[/COLOR] [COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, path))
    logging.log("[Path Check] ADDON_ID and plugin folder doesnt match. {0} / {1} ".format(CONFIG.ADDON_ID, path))
else:
    logging.log("[Path Check] Good!", level=xbmc.LOGNOTICE)

if CONFIG.KODIADDONS in CONFIG.ADDON_PATH:
    logging.log("Copying path to addons dir", level=xbmc.LOGNOTICE)
    if not os.path.exists(CONFIG.ADDONS):
        os.makedirs(CONFIG.ADDONS)
    if os.path.exists(CONFIG.PLUGIN):
        logging.log("Folder already exists, cleaning House", level=xbmc.LOGNOTICE)
        tools.clean_house(CONFIG.PLUGIN)
        tools.remove_folder(CONFIG.PLUGIN)
    try:
        tools.copytree(CONFIG.ADDON_PATH, CONFIG.PLUGIN)
    except:
        pass
    update.force_update(silent=True)

try:
    if not os.path.exists(CONFIG.MYBUILDS):
        xbmcvfs.mkdirs(CONFIG.MYBUILDS)
except:
    pass


### AUTO INSTALL REPO
logging.log("[Auto Install Repo] Started", level=xbmc.LOGNOTICE)
if CONFIG.AUTOINSTALL == 'Yes' and not os.path.exists(os.path.join(CONFIG.ADDONS, CONFIG.REPOID)):
    workingxml = tools.check_url(CONFIG.REPOADDONXML)
    if workingxml:
        ver = tools.parse_dom(tools.open_url(CONFIG.REPOADDONXML), 'addon', ret='version', attrs={'id': CONFIG.REPOID})
        if len(ver) > 0:
            installzip = '{0}-{1}.zip'.format(CONFIG.REPOID, ver[0])
            workingrepo = tools.check_url(CONFIG.REPOZIPURL+installzip)
            if workingrepo:
                gui.DP.create(CONFIG.ADDONTITLE, 'Downloading Repo...', '', 'Please Wait')
                if not os.path.exists(CONFIG.PACKAGES):
                    os.makedirs(CONFIG.PACKAGES)
                lib = os.path.join(CONFIG.PACKAGES, installzip)
                try:
                    os.remove(lib)
                except:
                    pass

                from resources.libs import downloader
                from resources.libs import extract
                downloader.download(CONFIG.REPOZIPURL+installzip, lib, gui.DP)
                extract.all(lib, CONFIG.ADDONS, gui.DP)

                try:
                    repoxml = os.path.join(CONFIG.ADDONS, CONFIG.REPOID, 'addon.xml')
                    name = tools.parse_dom(tools.read_from_file(repoxml), 'addon', ret='name', attrs={'id': CONFIG.REPOID})
                    logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, name[0]),
                                       "[COLOR {0}]Add-on updated[/COLOR]".format(CONFIG.COLOR2),
                                       icon=os.path.join(CONFIG.ADDONS, CONFIG.REPOID, 'icon.png'))
                except:
                    pass

                if CONFIG.KODIV >= 17:
                    db.addon_database(CONFIG.REPOID, 1)

                gui.DP.close()
                xbmc.sleep(500)
                update.force_update(silent=True)
                logging.log("[Auto Install Repo] Successfully Installed", level=xbmc.LOGNOTICE)
            else:
                logging.log_notify("[COLOR {0}]Repo Install Error[/COLOR]".format(CONFIG.COLOR1),
                                   "[COLOR {0}]Invalid url for zip![/COLOR]".format(CONFIG.COLOR2))
                logging.log("[Auto Install Repo] Was unable to create a working url for repository. {0}".format(workingrepo), level=xbmc.LOGERROR)
        else:
            logging.log("Invalid URL for Repo Zip", level=xbmc.LOGERROR)
    else:
        logging.log_notify("[COLOR {0}]Repo Install Error[/COLOR]".format(CONFIG.COLOR1),
                           "[COLOR {0}]Invalid addon.xml file![/COLOR]".format(CONFIG.COLOR2))
        logging.log("[Auto Install Repo] Unable to read the addon.xml file.", level=xbmc.LOGERROR)
elif not CONFIG.AUTOINSTALL == 'Yes':
    logging.log("[Auto Install Repo] Not Enabled", level=xbmc.LOGNOTICE)
elif os.path.exists(os.path.join(CONFIG.ADDONS, CONFIG.REPOID)):
    logging.log("[Auto Install Repo] Repository already installed")

### AUTO UPDATE WIZARD
logging.log("[Auto Update Wizard] Started", level=xbmc.LOGNOTICE)
if CONFIG.AUTOUPDATE == 'Yes':
    update.wizard_update('startup')
else:
    logging.log("[Auto Update Wizard] Not Enabled", level=xbmc.LOGNOTICE)

### NOTIFICATIONS
logging.log("[Notifications] Started", level=xbmc.LOGNOTICE)
if CONFIG.ENABLE == 'Yes':
    if not CONFIG.NOTIFY == 'true':
        url = tools.check_url(CONFIG.NOTIFICATION)
        if url:
            id, msg = gui.split_notify(CONFIG.NOTIFICATION)
            if id:
                try:
                    id = int(id)
                    if id == CONFIG.NOTEID:
                        if CONFIG.NOTEDISMISS == 'false':
                            gui.show_notification(msg)
                        else:
                            logging.log("[Notifications] id[{0}] Dismissed".format(int(id)), level=xbmc.LOGNOTICE)
                    elif id > CONFIG.NOTEID:
                        logging.log("[Notifications] id: {0}".format(str(id)), level=xbmc.LOGNOTICE)
                        CONFIG.set_setting('noteid', str(id))
                        CONFIG.set_setting('notedismiss', 'false')
                        gui.show_notification(msg=msg)
                        logging.log("[Notifications] Complete", level=xbmc.LOGNOTICE)
                except Exception as e:
                    logging.log("Error on Notifications Window: {0}".format(str(e)), level=xbmc.LOGERROR)
            else:
                logging.log("[Notifications] Text File not formatted Correctly")
        else:
            logging.log("[Notifications] URL({0}): {1}".format(CONFIG.NOTIFICATION, url), level=xbmc.LOGNOTICE)
    else:
        logging.log("[Notifications] Turned Off", level=xbmc.LOGNOTICE)
else:
    logging.log("[Notifications] Not Enabled", level=xbmc.LOGNOTICE)

### BUILD CHECK
logging.log("[Installed Check] Started", level=xbmc.LOGNOTICE)
if CONFIG.INSTALLED == 'true':
    if CONFIG.KODIV >= 17:
        db.kodi_17_fix()
        if CONFIG.SKIN in ['skin.confluence', 'skin.estuary', 'skin.estouchy']:
            check.check_skin()
        FAILED = True
    elif not CONFIG.EXTRACT == '100' and not CONFIG.BUILDNAME == "":
        logging.log("[Installed Check] Build was extracted {0}/100 with [ERRORS: {1}]".format(CONFIG.EXTRACT, CONFIG.EXTERROR), level=xbmc.LOGNOTICE)
        yes = gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                               '[COLOR {0}]{1}[/COLOR] [COLOR {2}]was not installed correctly!'.format(CONFIG.COLOR1, CONFIG.COLOR2, CONFIG.BUILDNAME),
                               'Installed: [COLOR {0}]{1}[/COLOR] / Error Count: [COLOR {2}]{3}[/COLOR]'.format(CONFIG.COLOR1, CONFIG.EXTRACT, CONFIG.COLOR1, CONFIG.EXTERROR),
                               'Would you like to try again?[/COLOR]',
                               nolabel='[B]No Thanks![/B]', yeslabel='[B]Retry Install[/B]')
        CONFIG.clear_setting('build')
        FAILED = True
        if yes:
            xbmc.executebuiltin("PlayMedia(plugin://{0}/?mode=install&name={1}&url=fresh)".format(CONFIG.ADDON_ID, quote_plus(CONFIG.BUILDNAME)))
            logging.log("[Installed Check] Fresh Install Re-activated", level=xbmc.LOGNOTICE)
        else:
            logging.log("[Installed Check] Reinstall Ignored")
    elif CONFIG.SKIN in ['skin.confluence', 'skin.estuary', 'skin.estouchy']:
        logging.log("[Installed Check] Incorrect skin: {0}".format(CONFIG.SKIN), level=xbmc.LOGNOTICE)
        defaults = CONFIG.get_setting('defaultskin')
        if not defaults == '':
            if os.path.exists(os.path.join(CONFIG.ADDONS, defaults)):
                if skin.skin_to_default(defaults):
                    skin.look_and_feel_data('restore')
        if not CONFIG.SKIN == defaults and not CONFIG.BUILDNAME == "":
            gui_xml = check.check_build(CONFIG.BUILDNAME, 'gui')
            FAILED = True
            if gui_xml == 'http://':
                logging.log("[Installed Check] Guifix was set to http://", level=xbmc.LOGNOTICE)
                gui.DIALOG.ok(CONFIG.ADDONTITLE,
                              "[COLOR {0}]It looks like the skin settings was not applied to the build.".format(CONFIG.COLOR2),
                              "Sadly no gui fix was attatched to the build",
                              "You will need to reinstall the build and make sure to do a force close[/COLOR]")
            elif tools.check_url(gui):
                yes = gui.DIALOG.yesno(CONFIG.ADDONTITLE,
                                       '{0} was not installed correctly!'.format(CONFIG.BUILDNAME),
                                       'It looks like the skin settings was not applied to the build.',
                                       'Would you like to apply the GuiFix?',
                                       nolabel='[B]No, Cancel[/B]', yeslabel='[B]Apply Fix[/B]')
                if yes:
                    xbmc.executebuiltin("PlayMedia(plugin://{0}/?mode=install&name={1}&url=gui)".format(CONFIG.ADDON_ID, quote_plus(CONFIG.BUILDNAME)))
                    logging.log("[Installed Check] Guifix attempting to install")
                else:
                    logging.log('[Installed Check] Guifix url working but cancelled: {0}'.format(gui), level=xbmc.LOGNOTICE)
            else:
                gui.DIALOG.ok(CONFIG.ADDONTITLE,
                              "[COLOR {0}]It looks like the skin settings was not applied to the build.".format(CONFIG.COLOR2),
                              "Sadly no gui fix was attatched to the build",
                              "You will need to reinstall the build and make sure to do a force close[/COLOR]")
                logging.log('[Installed Check] Guifix url not working: {0}'.format(gui), level=xbmc.LOGNOTICE)
    else:
        logging.log('[Installed Check] Install seems to be completed correctly', level=xbmc.LOGNOTICE)
    if not CONFIG.get_setting('pvrclient') == "":
        db.toggle_addon(CONFIG.get_setting('pvrclient'), 1)
        xbmc.executebuiltin('StartPVRManager')
    update.addon_updates('reset')

    if CONFIG.KEEPTRAKT == 'true':
        from resources.libs import traktit
        traktit.trakt_it('restore', 'all')
        logging.log('[Installed Check] Restoring Trakt Data', level=xbmc.LOGNOTICE)
    if CONFIG.KEEPDEBRID == 'true':
        from resources.libs import debridit
        debridit.debrid_it('restore', 'all')
        logging.log('[Installed Check] Restoring Real Debrid Data', level=xbmc.LOGNOTICE)
    if CONFIG.KEEPLOGIN == 'true':
        from resources.libs import loginit
        loginit.login_it('restore', 'all')
        logging.log('[Installed Check] Restoring Login Data', level=xbmc.LOGNOTICE)
    CONFIG.clear_setting('install')
else:
    logging.log("[Installed Check] Not Enabled", level=xbmc.LOGNOTICE)

if not FAILED:
    logging.log("[Build Check] Started", level=xbmc.LOGNOTICE)
    if not tools.check_url(CONFIG.BUILDFILE):
        logging.log("[Build Check] Not a valid URL for Build File: {0}".format(CONFIG.BUILDFILE), level=xbmc.LOGNOTICE)
    elif CONFIG.BUILDCHECK == '' and CONFIG.BUILDNAME == '':
        logging.log("[Build Check] First Run", level=xbmc.LOGNOTICE)
        gui.show_save_data_settings()
        gui.show_build_prompt()
        CONFIG.set_setting('lastbuildcheck', str(tools.get_date(days=CONFIG.UPDATECHECK)))
    elif not CONFIG.BUILDNAME == '':
        logging.log("[Build Check] Build Installed", level=xbmc.LOGNOTICE)
        if CONFIG.SKIN in ['skin.confluence', 'skin.estuary', 'skin.estouchy'] and not CONFIG.DEFAULTIGNORE == 'true':
            check.check_skin()
            logging.log("[Build Check] Build Installed: Checking Updates", level=xbmc.LOGNOTICE)
            CONFIG.set_setting('lastbuildcheck', str(tools.get_date(days=CONFIG.UPDATECHECK)))
            check.check_build_update()
        elif CONFIG.BUILDCHECK <= str(tools.get_date()):
            logging.log("[Build Check] Build Installed: Checking Updates", level=xbmc.LOGNOTICE)
            CONFIG.set_setting('lastbuildcheck', str(tools.get_date(days=CONFIG.UPDATECHECK)))
            check.check_build_update()
        else:
            logging.log("[Build Check] Build Installed: Next check isn't until: {0} / TODAY is: {1}".format(CONFIG.BUILDCHECK, str(tools.get_date())), level=xbmc.LOGNOTICE)

### SAVE TRAKT
logging.log("[Trakt Data] Started", level=xbmc.LOGNOTICE)
if CONFIG.KEEPTRAKT == 'true':
    if CONFIG.TRAKTSAVE <= str(tools.get_date()):
        from resources.libs import traktit
        logging.log("[Trakt Data] Saving all Data", level=xbmc.LOGNOTICE)
        traktit.auto_update('all')
        CONFIG.set_setting('traktlastsave', str(tools.get_date(days=3)))
    else:
        logging.log("[Trakt Data] Next Auto Save isn't until: {0} / TODAY is: {1}".format(CONFIG.TRAKTSAVE, str(tools.get_date())), level=xbmc.LOGNOTICE)
else:
    logging.log("[Trakt Data] Not Enabled", level=xbmc.LOGNOTICE)

### SAVE DEBRID
logging.log("[Debrid Data] Started", level=xbmc.LOGNOTICE)
if CONFIG.KEEPDEBRID == 'true':
    if CONFIG.DEBRIDSAVE <= str(tools.get_date()):
        from resources.libs import debridit
        logging.log("[Debrid Data] Saving all Data", level=xbmc.LOGNOTICE)
        debridit.auto_update('all')
        CONFIG.set_setting('debridlastsave', str(tools.get_date(days=3)))
    else:
        logging.log("[Debrid Data] Next Auto Save isn't until: {0} / TODAY is: {1}".format(CONFIG.DEBRIDSAVE, str(tools.get_date())), level=xbmc.LOGNOTICE)
else:
    logging.log("[Debrid Data] Not Enabled", level=xbmc.LOGNOTICE)

### SAVE LOGIN
logging.log("[Login Info] Started", level=xbmc.LOGNOTICE)
if CONFIG.KEEPLOGIN == 'true':
    if CONFIG.LOGINSAVE <= str(tools.get_date()):
        from resources.libs import loginit
        logging.log("[Login Info] Saving all Data", level=xbmc.LOGNOTICE)
        loginit.auto_update('all')
        CONFIG.set_setting('loginlastsave', str(tools.get_date(days=3)))
    else:
        logging.log("[Login Info] Next Auto Save isn't until: {0} / TODAY is: {1}".format(CONFIG.LOGINSAVE, str(tools.get_date())), level=xbmc.LOGNOTICE)
else:
    logging.log("[Login Info] Not Enabled", level=xbmc.LOGNOTICE)

### AUTO CLEAN
logging.log("[Auto Clean Up] Started", level=xbmc.LOGNOTICE)
if CONFIG.AUTOCLEANUP == 'true':
    service = False
    days = [tools.get_date(), tools.get_date(days=1), tools.get_date(days=3), tools.get_date(days=7)]

    feq = int(float(CONFIG.AUTOFREQ))

    if CONFIG.AUTONEXTRUN <= str(tools.get_date()) or feq == 0:
        service = True
        next_run = days[feq]
        CONFIG.set_setting('nextautocleanup', str(next_run))
    else:
        logging.log("[Auto Clean Up] Next Clean Up {0}".format(CONFIG.AUTONEXTRUN), level=xbmc.LOGNOTICE)
    if service:
        if CONFIG.AUTOCACHE == 'true':
            logging.log('[Auto Clean Up] Cache: On', level=xbmc.LOGNOTICE)
            clear.clear_cache(True)
        else:
            logging.log('[Auto Clean Up] Cache: Off', level=xbmc.LOGNOTICE)
        if CONFIG.AUTOTHUMBS == 'true':
            logging.log('[Auto Clean Up] Old Thumbs: On', level=xbmc.LOGNOTICE)
            clear.old_thumbs()
        else:
            logging.log('[Auto Clean Up] Old Thumbs: Off', level=xbmc.LOGNOTICE)
        if CONFIG.AUTOPACKAGES == 'true':
            logging.log('[Auto Clean Up] Packages: On', level=xbmc.LOGNOTICE)
            clear.clear_packages_startup()
        else:
            logging.log('[Auto Clean Up] Packages: Off', level=xbmc.LOGNOTICE)
else:
    logging.log('[Auto Clean Up] Turned off', level=xbmc.LOGNOTICE)

