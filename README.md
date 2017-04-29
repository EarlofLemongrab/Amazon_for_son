# Amazon_Server
## TODO
1.完成daemon部分load request的逻辑（检查DB内的arrive，以及ready，两个条件都满足时，将load command放入消息队列） <br />
2.考虑如何在收到ready时，发送load的情况下拿到正确的truck_id（也许可以改下数据库，把arrive改成int类型，没有arrive的时候，默认为－1） <br />
3.etc...... <br />
