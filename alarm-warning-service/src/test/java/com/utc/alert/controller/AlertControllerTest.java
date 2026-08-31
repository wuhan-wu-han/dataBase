package com.utc.alert.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.utc.alert.dto.request.UpdateAlertStatusRequest;
import com.utc.alert.dto.response.AlertResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.service.AlertService;
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
class AlertControllerTest {

    @Mock
    private AlertService alertService;

    @InjectMocks
    private AlertController alertController;

    private MockMvc mockMvc;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @org.junit.jupiter.api.BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.standaloneSetup(alertController)
                .setControllerAdvice(new com.utc.alert.common.exception.GlobalExceptionHandler())
                .setValidator(new org.springframework.validation.beanvalidation.LocalValidatorFactoryBean())
                .build();
    }

    @Test
    void getAlerts_returnsList() throws Exception {
        PageResponse<AlertResponse> pageResponse = new PageResponse<>();
        pageResponse.setRecords(Collections.emptyList());
        pageResponse.setTotal(0);
        pageResponse.setPage(1);
        pageResponse.setSize(10);
        pageResponse.setPages(0);
        when(alertService.getAlerts(any())).thenReturn(pageResponse);

        mockMvc.perform(get("/api/alerts").param("page", "1").param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.total").value(0));
    }

    @Test
    void getAlertById_returnsAlert() throws Exception {
        AlertResponse response = new AlertResponse();
        response.setId(1L);
        response.setAlertLevel("RED");
        when(alertService.getAlertById(1L)).thenReturn(response);

        mockMvc.perform(get("/api/alerts/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.alertLevel").value("RED"));
    }

    @Test
    void updateAlertStatus_validRequest_succeeds() throws Exception {
        AlertResponse response = new AlertResponse();
        response.setId(1L);
        response.setAlertStatus("ACKNOWLEDGED");
        when(alertService.updateAlertStatus(eq(1L), any())).thenReturn(response);

        UpdateAlertStatusRequest request = new UpdateAlertStatusRequest();
        request.setStatus("ACKNOWLEDGED");

        mockMvc.perform(patch("/api/alerts/1/status")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.alertStatus").value("ACKNOWLEDGED"));
    }

    @Test
    void updateAlertStatus_blankStatus_returns400() throws Exception {
        UpdateAlertStatusRequest request = new UpdateAlertStatusRequest();
        request.setStatus("");

        mockMvc.perform(patch("/api/alerts/1/status")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(400));
    }
}
