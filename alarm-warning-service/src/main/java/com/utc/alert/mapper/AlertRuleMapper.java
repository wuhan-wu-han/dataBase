package com.utc.alert.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.utc.alert.entity.AlertRule;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

public interface AlertRuleMapper extends BaseMapper<AlertRule> {

    @Select("SELECT * FROM alert_rule WHERE enabled = 1 AND device_type = #{deviceType} "
            + "AND (area_id = #{areaId} OR area_id IS NULL)")
    List<AlertRule> selectMatchingRules(@Param("deviceType") String deviceType,
                                        @Param("areaId") String areaId);
}
