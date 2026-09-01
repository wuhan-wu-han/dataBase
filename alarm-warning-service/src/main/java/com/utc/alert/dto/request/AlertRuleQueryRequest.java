package com.utc.alert.dto.request;

import lombok.Data;

@Data
public class AlertRuleQueryRequest {

    private Integer page = 1;

    private Integer size = 10;

    private String deviceType;

    private String alertLevel;

    private Boolean enabled;
}
