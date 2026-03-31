<template>
  <el-dialog
    v-model="visible"
    title="发货核对"
    width="720px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    append-to-body
  >
    <div class="check-dialog">
      <div class="check-tip">
        <el-icon class="check-tip__icon"><WarningFilled /></el-icon>
        <span>以下商品发货数量与备货、下单数量不一致，请核对确认</span>
      </div>

      <el-table
        :data="rows"
        border
        max-height="320"
        style="width: 100%"
        :header-cell-style="{
          background: 'var(--el-fill-color-light)',
          color: 'var(--el-text-color-primary)'
        }"
      >
        <el-table-column
          prop="skuName"
          label="商品名称"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column
          prop="skuCode"
          label="SKU编码"
          min-width="160"
          show-overflow-tooltip
        />
        <el-table-column prop="orderQty" label="下单数量" min-width="100" />
        <el-table-column prop="availableQty" label="备货数量" min-width="100" />
        <el-table-column prop="deliverQty" label="发货数量" min-width="100" />
      </el-table>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">再次核对</el-button>
        <el-button type="primary" @click="handleConfirm">已确认无误</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { WarningFilled } from "@element-plus/icons-vue";

defineProps<{
  rows: Array<Record<string, any>>;
}>();

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
  name: "CheckDialog"
};
</script>

<style scoped>
.check-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.check-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  line-height: 20px;
}

.check-tip__icon {
  color: #e6a23c;
  font-size: 18px;
  flex-shrink: 0;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.dialog-footer .el-button {
  min-width: 120px;
}
</style>
