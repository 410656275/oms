#!/bin/bash


function status {
  ps axuf |grep "uwsgi" |grep -v grep
}


function start {
  uwsgi --ini uwsgi.ini
}


function stop {
  pid=$(ps aux |grep "uwsgi.ini" |grep -v grep |awk '{print $2}' |xargs)

  if [[ ! -z "$pid" ]]; then
    kill -9 $pid >/dev/null 2>&1
  fi
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
    status
    start
    status
    ;;
  *)
    echo "Usage: bash $0 {status|start|stop|restart}"
    ;;
esac
