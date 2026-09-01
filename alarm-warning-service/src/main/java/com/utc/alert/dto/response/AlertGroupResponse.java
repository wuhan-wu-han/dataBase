package com.utc.alert.dto.response;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AlertGroupResponse {

    private Long id;
    private String groupCode;
    private String areaId;
    private String zone;
    private String highestLevel;
    private Integer totalCount;
    private String groupStatus;
    private LocalDateTime windowStart;
    private LocalDateTime windowEnd;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
