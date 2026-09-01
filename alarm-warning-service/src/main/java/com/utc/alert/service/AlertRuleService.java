package com.utc.alert.service;

import com.utc.alert.dto.request.AlertRuleQueryRequest;
import com.utc.alert.dto.request.CreateAlertRuleRequest;
import com.utc.alert.dto.request.UpdateAlertRuleRequest;
import com.utc.alert.dto.response.AlertRuleResponse;
import com.utc.alert.dto.response.PageResponse;

public interface AlertRuleService {

    PageResponse<AlertRuleResponse> getRules(AlertRuleQueryRequest request);

    AlertRuleResponse createRule(CreateAlertRuleRequest request);

    AlertRuleResponse updateRule(Long id, UpdateAlertRuleRequest request);

    void deleteRule(Long id);
}
