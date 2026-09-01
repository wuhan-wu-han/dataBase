package com.utc.alert.dto.request;

import lombok.Data;

@Data
public class AlertGroupQueryRequest {

    private Integer page = 1;

    private Integer size = 10;

    private String areaId;
}
