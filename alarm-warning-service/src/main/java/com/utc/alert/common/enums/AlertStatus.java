package com.utc.alert.common.enums;

import lombok.Getter;

@Getter
public enum AlertStatus {

    OPEN(0, "待处理"),
    ACKNOWLEDGED(1, "已确认"),
    RESOLVED(2, "已解决"),
    CLOSED(3, "已关闭");

    private final int code;
    private final String desc;

    AlertStatus(int code, String desc) {
        this.code = code;
        this.desc = desc;
    }
}
