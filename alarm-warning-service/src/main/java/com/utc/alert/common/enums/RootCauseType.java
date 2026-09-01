package com.utc.alert.common.enums;

import lombok.Getter;

@Getter
public enum RootCauseType {

    PRESSURE_ABNORMAL("压力异常"),
    TEMPERATURE_ABNORMAL("温度异常"),
    GAS_LEAK("气体泄漏"),
    CORROSION("腐蚀"),
    THIRD_PARTY_DAMAGE("第三方破坏"),
    UNKNOWN("未知");

    private final String desc;

    RootCauseType(String desc) {
        this.desc = desc;
    }
}
