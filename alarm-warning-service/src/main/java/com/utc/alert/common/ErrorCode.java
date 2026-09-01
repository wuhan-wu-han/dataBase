package com.utc.alert.common;

import lombok.Getter;

@Getter
public enum ErrorCode {

    RULE_NOT_FOUND(40201, "预警规则不存在"),
    RULE_DISABLED(40202, "预警规则已停用"),
    THRESHOLD_INVALID(40203, "阈值配置不合法"),
    EVENT_NOT_FOUND(40204, "预警事件不存在"),
    ILLEGAL_STATUS_TRANSITION(40205, "预警状态流转不合法"),
    PREDICTION_NOT_FOUND(40206, "预测记录不存在");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }
}
