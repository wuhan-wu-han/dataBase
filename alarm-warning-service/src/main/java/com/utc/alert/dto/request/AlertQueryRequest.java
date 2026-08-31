package com.utc.alert.dto.request;

import lombok.Data;

@Data
public class AlertQueryRequest {

    private Integer page = 1;

    private Integer size = 10;

    private String alertLevel;

    private String status;

    private String areaId;
}
