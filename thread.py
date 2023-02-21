# thread.py

import adsk.core, adsk.fusion, traceback, threading,  time
from . import utils, command


_myEventId = 'MyCustomEventId'

_my_event = None
_my_handler = None
_thread = None   

_running = True
_in_event = False


class onMyEvent(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
  
        ui = None
        global _in_event, _running

        try:

            app = adsk.core.Application.get()
            ui = app.userInterface
            
            if _in_event: 
                return
            _in_event = True

            # if we nave not failed before, and
            # the window is still open, 
            # increment the value so that onExecutePreviow() 
            # will be called

            if _running and command._the_step:
                command._the_step.value += 1

                # old way: bump the step and call the slice() directly
                # animation.step += 1
                # _running = animation.slice()
            
            _in_event = False

        except:

            if ui:
                ui.messageBox('thread.onMyEvent() Failed:\n{}'.format(traceback.format_exc()))
            _running = False
            


class myThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopped = False
        utils.trace("thread inited")
    
    def run(self):
        utils.trace("thread starting")

        global _running,_in_event
        while _running and not self.stopped:
            
            time.sleep(0.03)
                # 20 frames/second
                # without _in_event re-entrancy protection,
                # any quicker than this and fusion just crashes and exits !?!
            if not _in_event:
                app = adsk.core.Application.get()
                app.fireCustomEvent(_myEventId)
            
        utils.trace("thread_finished running=" + str(_running) + " self.stopped=" + str(self.stopped)) 
    
    def stop(self):
        utils.trace("thread stopping")
        self.stopped = True


def startThread():
    utils.trace("startThread() started ...")
    
    app = adsk.core.Application.get()
    global _my_event, _my_handler, _thread
    
    _my_event = app.registerCustomEvent(_myEventId)
    _my_handler = onMyEvent()
    _my_event.add(_my_handler)

    _thread = myThread()
    _thread.start()

    utils.trace("startThread() finished")
    

def stopThread():
    utils.trace("stopThread() started")

    global _my_event, _my_handler, _thread
    if _my_event:
        if _my_handler:
            utils.trace("removing _my_handler")
            _my_event.remove(_my_handler)
            _my_handler = None
      
        utils.trace("unregistring _myEventId")  
        app = adsk.core.Application.get()
        app.unregisterCustomEvent(_myEventId)
        _my_event = None

    if _thread:
        utils.trace("stopping _thread")
        _thread.stop()
        _thread = None

    utils.trace("stopThread() finished")
    

# end of thread.py
