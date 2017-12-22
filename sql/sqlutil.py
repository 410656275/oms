# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import os
import traceback
from django.conf import settings


logger = logging.getLogger(__name__)


def delete_file(file_path):
    logger.info('file_path, {0}'.format(file_path))

    try:
        x = os.path.normpath(
            os.path.join(settings.DATA_DIR, file_path)
        )
        logger.info('rm {0}'.format(x))
        os.remove(x)

        y = x.rsplit('/', 1)[0]
        if len(os.listdir(y)) == 0:
            logger.info('rmdir {0}'.format(y))
            os.rmdir(y)
        else:
            logger.info('skip rmdir {0}'.format(y))

        z = y.rsplit('/', 1)[0]
        if len(os.listdir(z)) == 0:
            logger.info('rmdir {0}'.format(z))
            os.rmdir(z)
        else:
            logger.info('skip rmdir {0}'.format(z))
    except:
        logger.error(traceback.format_exc())
