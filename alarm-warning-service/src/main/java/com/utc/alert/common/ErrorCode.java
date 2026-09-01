package com.utc.alert.common;

import lombok.Getter;

@Getter
public enum ErrorCode {

    PARAM_ERROR(40201, "参数错误"),
    DATA_NOT_FOUND(40202, "数据不存在"),
    KAFKA_MESSAGE_PARSE_ERROR(40203, "Kafka消息解析失败"),
    DATABASE_ERROR(40204, "数据库异常"),
    ILLEGAL_STATUS_TRANSITION(40205, "非法状态流转");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }
}
