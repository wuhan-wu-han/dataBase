package com.utc.alert.dto.response;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class AreaPriorityResponse {

    private Long id;
    private String areaId;
    private String areaName;
    private Integer importance;
    private BigDecimal populationWeight;
    private String description;
}
