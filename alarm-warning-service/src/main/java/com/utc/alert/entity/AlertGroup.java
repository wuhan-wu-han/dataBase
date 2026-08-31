package com.utc.alert.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("alert_group")
public class AlertGroup {

    @TableId(type = IdType.AUTO)
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
