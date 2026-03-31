<template>
  <el-dialog
    v-model="visible"
    title="发货确认"
    width="480px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    append-to-body
    class="confirm-dialog"
  >
    <div class="confirm-content">
      <div class="confirm-header">
        <el-icon class="header-icon"><WarningFilled /></el-icon>
        <span class="header-text">确认发货前请核对以下事项</span>
      </div>
      <div class="checklist-card">
        <div class="check-item">
          <el-icon class="check-icon"><CircleCheck /></el-icon>
          <span>当前订单所需商品已完成备货</span>
        </div>
        <div class="check-item">
          <el-icon class="check-icon"><CircleCheck /></el-icon>
          <span>已完成实际发货数量清点与录入</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">再次核对</el-button>
        <el-button type="primary" @click="handleConfirm">确认提交</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { CircleCheck, WarningFilled } from "@element-plus/icons-vue";

const visible = defineModel<boolean>("visible", { required: true });

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

function handleConfirm() {
  emit("confirm");
  visible.value = false;
}

function handleCancel() {
  emit("cancel");
  visible.value = false;
}
</script>

<script lang="ts">
export default {
  name: "ConfirmDialog"
};
</script>

<style scoped>
.confirm-dialog :deep(.el-dialog__header) {
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.confirm-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.confirm-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.confirm-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.confirm-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 20px;
  color: #e6a23c;
}

.header-text {
  font-size: 15px;
  color: #303133;
  font-weight: 500;
}

.checklist-card {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #606266;
}

.check-icon {
  font-size: 16px;
  color: #67c23a;
  flex-shrink: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer .el-button {
  min-width: 100px;
}
</style>
