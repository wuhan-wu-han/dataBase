package com.utc.alert.service;

import com.utc.alert.dto.MatchResult;
import com.utc.alert.dto.kafka.KafkaMessage;

import java.util.List;

public interface RuleMatchService {

    List<MatchResult> matchRules(KafkaMessage message);
}
