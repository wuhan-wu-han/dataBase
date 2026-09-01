package com.utc.alert.common.enums;

import lombok.Getter;

@Getter
public enum EventType {

    SENSOR_DATA("传感器数据"),
    ALARM_EVENT("告警事件"),
    GAS_RISK_EVENT("燃气风险事件"),
    ALERT_CREATED("预警事件");

    private final String desc;

    EventType(String desc) {
        this.desc = desc;
    }
}
