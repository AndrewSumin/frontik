import functools
import threading
import Queue
import tornado.ioloop
import multiprocessing
import frontik.handler_xml
from frontik import etree

import logging
log = logging.getLogger('frontik.jobs')
XSL_cache = None

def work(filename, data):
    global XSL_cache
    try:
        transform = XSL_cache.xsl_cache.load(filename)
        result = str(transform(etree.fromstring(data)))
    except Exception, e:
#        self.log.debug('Failed transformation XSL: '+filename)        
        return (None, e)
    return (result, None)

def init(cache_config):
    global XSL_cache
    XSL_cache = frontik.handler_xml.PageHandlerXMLGlobals(cache_config)

class ProcessPoolExecutor(object):
    def __init__(self, pool_size, cache_config):
        self.log = log
        self.log.debug('pool size: '+str(pool_size))
        self.workers = multiprocessing.Pool(pool_size, init, [cache_config])
        self.log.debug('active process count = ' + str(len(multiprocessing.active_children())))

    def add_job(self, filename, data, cb, err_cb):
        def _cb(responce):
            r, e = responce
            if r is not None:
                cb(r)
            else:
                err_cb(e)
        self.workers.apply_async(work, [filename, etree.tostring(data)], callback = _cb) #, error_callback = err_cb)
