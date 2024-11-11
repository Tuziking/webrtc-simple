package com.webrtc;


import com.alibaba.fastjson2.JSONObject;
import com.corundumstudio.socketio.Configuration;
import com.corundumstudio.socketio.SocketIOClient;
import com.corundumstudio.socketio.SocketIOServer;
import com.webrtc.bean.ContactInfo;

import java.util.HashMap;
import java.util.Map;

public class Main {
    // 客户端映射
    private static Map<String, SocketIOClient> clientMap = new HashMap<>();
    // 人员名字映射
    private static Map<String, String> nameMap = new HashMap<>();


    public static void main(String[] args) {
        Configuration config = new Configuration();
        // 如果调用了setHostname方法，就只能通过主机名访问，不能通过IP访问
        //config.setHostname("localhost");
        config.setPort(9999); // 设置监听端口
        final SocketIOServer server = new SocketIOServer(config);
        // 添加连接连通的监听事件
        server.addConnectListener(client -> {
            System.out.println(client.getSessionId().toString()+"已连接");
            clientMap.put(client.getSessionId().toString(), client);
        });
        // 添加连接断开的监听事件
        server.addDisconnectListener(client -> {
            System.out.println(client.getSessionId().toString()+"已断开");
            for (Map.Entry<String, SocketIOClient> item : clientMap.entrySet()) {
                if (client.getSessionId().toString().equals(item.getKey())) {
                    clientMap.remove(item.getKey());
                    break;
                }
            }
            nameMap.remove(client.getSessionId().toString());
        });
        // 添加用户上线的事件监听器
        server.addEventListener("self_online", String.class, (client, name, ackSender) -> {
            System.out.println(client.getSessionId().toString()+"已上线："+name);
            for (Map.Entry<String, SocketIOClient> item : clientMap.entrySet()) {
                if (!client.getSessionId().toString().equals(item.getKey())) {
                    item.getValue().sendEvent("friend_online", name);
                    client.sendEvent("friend_online", nameMap.get(item.getKey()));
                }
            }
            nameMap.put(client.getSessionId().toString(), name);
        });

        // 添加用户下线的事件监听器
        server.addEventListener("self_offline", String.class, (client, name, ackSender) -> {
            System.out.println(client.getSessionId().toString()+"已下线："+name);
            for (Map.Entry<String, SocketIOClient> item : clientMap.entrySet()) {
                if (!client.getSessionId().toString().equals(item.getKey())) {
                    item.getValue().sendEvent("friend_offline", name);
                }
            }
            nameMap.remove(client.getSessionId().toString());
        });

        // 添加ICE候选的事件监听器
        server.addEventListener("IceInfo", JSONObject.class, (client, json, ackSender) -> {
            System.out.println(client.getSessionId().toString()+"ICE候选："+json.toString());
            String destId = json.getString("destination");
            for (Map.Entry<String, String> item : nameMap.entrySet()) {
                if (destId.equals(item.getValue())) {
                    clientMap.get(item.getKey()).sendEvent("IceInfo", json);
                    break;
                }
            }
        });

        // 添加SDP媒体的事件监听器
        server.addEventListener("SdpInfo", JSONObject.class, (client, json, ackSender) -> {
//            System.out.println(client.getSessionId().toString()+"SDP媒体："+json.toString());
            String destId = json.getString("destination");
            for (Map.Entry<String, String> item : nameMap.entrySet()) {
                if (destId.equals(item.getValue())) {
                    clientMap.get(item.getKey()).sendEvent("SdpInfo", json);
                    break;
                }
            }
        });

        //待接收的：offer_converse提出通话、self_dial_in我方接通、self_hang_up我方挂断
        //待发送的：friend_converse通话请求、other_dial_in对方接通、other_hang_up对方挂断
        // 添加通话请求的事件监听器
        server.addEventListener("offer_converse", JSONObject.class, (client, json, ackSender) -> {
            System.out.println(client.getSessionId().toString()+"提出通话："+json.toString());
            ContactInfo contact = (ContactInfo) JSONObject.parseObject(String.valueOf(json), ContactInfo.class);
            for (Map.Entry<String, String> item : nameMap.entrySet()) {
                if (contact.getTo().equals(item.getValue())) {
                    clientMap.get(item.getKey()).sendEvent("friend_converse", contact.getFrom());
                    break;
                }
            }
        });

        // 添加通话拨入的事件监听器
        server.addEventListener("self_dial_in", JSONObject.class, (client, json, ackSender) -> {
            System.out.println(client.getSessionId().toString()+"接受通话："+json.toString());
            ContactInfo contact = (ContactInfo) JSONObject.parseObject(String.valueOf(json), ContactInfo.class);
            nameMap.put(client.getSessionId().toString(), contact.getFrom());
            for (Map.Entry<String, String> item : nameMap.entrySet()) {
                if (contact.getTo().equals(item.getValue())) {
                    clientMap.get(item.getKey()).sendEvent("other_dial_in", contact.getFrom());
                    break;
                }
            }
        });

        // 添加通话挂断的事件监听器
        server.addEventListener("self_hang_up", JSONObject.class, (client, json, ackSender) -> {
            System.out.println(client.getSessionId().toString()+"挂断通话："+json.toString());
            ContactInfo contact = (ContactInfo) JSONObject.parseObject(String.valueOf(json), ContactInfo.class);
            for (Map.Entry<String, String> item : nameMap.entrySet()) {
                if (contact.getTo().equals(item.getValue())) {
                    clientMap.get(item.getKey()).sendEvent("other_hang_up", contact.getFrom());
                    break;
                }
            }
        });
        server.start(); // 启动Socket服务
//        System.out.println("Hello world!");
    }
}