package com.utc.alert.common.enums;

import lombok.Getter;

@Getter
public enum AlertLevel {

    BLUE(1, "蓝色预警"),
    YELLOW(2, "黄色预警"),
    ORANGE(3, "橙色预警"),
    RED(4, "红色预警");

    private final int code;
    private final String desc;

    AlertLevel(int code, String desc) {
        this.code = code;
        this.desc = desc;
    }
}
