package com.utc.alert.controller;

import com.utc.alert.dto.response.AlertGroupResponse;
import com.utc.alert.dto.response.PageResponse;
import com.utc.alert.service.AlertGroupService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class AlertGroupControllerTest {

    @Mock
    private AlertGroupService alertGroupService;

    @InjectMocks
    private AlertGroupController alertGroupController;

    private MockMvc mockMvc;

    @org.junit.jupiter.api.BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.standaloneSetup(alertGroupController)
                .setControllerAdvice(new com.utc.alert.common.exception.GlobalExceptionHandler())
                .build();
    }

    @Test
    void getGroups_returnsList() throws Exception {
        PageResponse<AlertGroupResponse> pageResponse = new PageResponse<>();
        pageResponse.setRecords(Collections.emptyList());
        pageResponse.setTotal(0);
        pageResponse.setPage(1);
        pageResponse.setSize(10);
        pageResponse.setPages(0);
        when(alertGroupService.getGroups(any())).thenReturn(pageResponse);

        mockMvc.perform(get("/api/alert-groups").param("page", "1").param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.total").value(0));
    }

    @Test
    void getGroupById_returnsGroup() throws Exception {
        AlertGroupResponse response = new AlertGroupResponse();
        response.setId(1L);
        response.setAreaId("AREA-A01");
        when(alertGroupService.getGroupById(1L)).thenReturn(response);

        mockMvc.perform(get("/api/alert-groups/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.areaId").value("AREA-A01"));
    }
}
