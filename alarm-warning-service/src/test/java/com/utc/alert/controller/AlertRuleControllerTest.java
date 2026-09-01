package com.utc.alert.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.utc.alert.dto.request.CreateAlertRuleRequest;
import com.utc.alert.dto.request.UpdateAlertRuleRequest;
import com.utc.alert.dto.response.AlertRuleResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.service.AlertRuleService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class AlertRuleControllerTest {

    @Mock
    private AlertRuleService alertRuleService;

    @InjectMocks
    private AlertRuleController alertRuleController;

    private MockMvc mockMvc;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @org.junit.jupiter.api.BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.standaloneSetup(alertRuleController)
                .setControllerAdvice(new com.utc.alert.common.exception.GlobalExceptionHandler())
                .setValidator(new org.springframework.validation.beanvalidation.LocalValidatorFactoryBean())
                .build();
    }

    @Test
    void getRules_returnsList() throws Exception {
        PageResponse<AlertRuleResponse> pageResponse = new PageResponse<>();
        pageResponse.setRecords(Collections.emptyList());
        pageResponse.setTotal(0);
        pageResponse.setPage(1);
        pageResponse.setSize(10);
        pageResponse.setPages(0);
        when(alertRuleService.getRules(any())).thenReturn(pageResponse);

        mockMvc.perform(get("/api/alert-rules"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void createRule_validRequest_succeeds() throws Exception {
        AlertRuleResponse response = new AlertRuleResponse();
        response.setId(1L);
        response.setRuleCode("RULE-001");
        when(alertRuleService.createRule(any())).thenReturn(response);

        CreateAlertRuleRequest request = new CreateAlertRuleRequest();
        request.setRuleCode("RULE-001");
        request.setRuleName("压力规则");
        request.setDeviceType("PRESSURE");
        request.setMetricKey("pressure");
        request.setCompareType("GT");

        mockMvc.perform(post("/api/alert-rules")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.ruleCode").value("RULE-001"));
    }

    @Test
    void createRule_missingRequiredFields_returns400() throws Exception {
        CreateAlertRuleRequest request = new CreateAlertRuleRequest();

        mockMvc.perform(post("/api/alert-rules")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(400));
    }

    @Test
    void updateRule_validRequest_succeeds() throws Exception {
        AlertRuleResponse response = new AlertRuleResponse();
        response.setId(1L);
        response.setRuleName("更新规则");
        when(alertRuleService.updateRule(eq(1L), any())).thenReturn(response);

        UpdateAlertRuleRequest request = new UpdateAlertRuleRequest();
        request.setRuleName("更新规则");
        request.setDeviceType("PRESSURE");
        request.setMetricKey("pressure");
        request.setCompareType("GT");

        mockMvc.perform(put("/api/alert-rules/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.ruleName").value("更新规则"));
    }

    @Test
    void deleteRule_succeeds() throws Exception {
        doNothing().when(alertRuleService).deleteRule(1L);

        mockMvc.perform(delete("/api/alert-rules/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }
}
