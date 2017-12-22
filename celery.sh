#!/bin/bash


function status {
  ps axuf |grep celery |grep -v grep
}


function start {
  if [ ! -f celery.sh ]; then
    echo "Doesn't support relative path"
    exit 1
  fi

  if [ $(ps axu |grep celery |grep worker |wc -l) -ne 0 ]; then
    echo "Celery process alread exists"
    exit 2
  fi

  nohup celery -A project worker -l INFO -f logs/celery.log >>logs/celery.log 2>&1 &
}


function stop {
  ps axu |grep celery |grep worker |awk '{print $2}' |xargs kill -9 >/dev/null 2>&1
}


case $1 in
  status)
    status
    ;;
  start)
    start
    status
    ;;
  stop)
    stop
    status
    ;;
  restart)
    stop
    start
    status
    ;;
  *)
    echo "Usage: $0 {status|start|stop|restart}"
    ;;
esac
