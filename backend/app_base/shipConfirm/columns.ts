import type { PlusColumn } from "plus-pro-components";

export const STATUS_OPTIONS = [
  { label: "全部状态", value: "" },
  { label: "待确认", value: "PENDING" },
  { label: "已确认", value: "CONFIRMED" },
  { label: "已撤销", value: "CANCELED" }
];

export const searchColumns: PlusColumn[] = [
  {
    label: "发货确认单编号",
    prop: "code",
    valueType: "input",
    colProps: { span: 6 },
    fieldProps: { placeholder: "请输入发货确认单编号", clearable: true }
  },
  {
    label: "来源编号",
    prop: "mallOrderId",
    valueType: "input",
    colProps: { span: 6 },
    fieldProps: { placeholder: "请输入来源编号", clearable: true }
  },
  {
    label: "单据状态",
    prop: "status",
    valueType: "select",
    colProps: { span: 6 },
    fieldProps: {
      placeholder: "请选择单据状态",
      clearable: true
    },
    options: STATUS_OPTIONS
  },
  {
    label: "计划发货日",
    prop: "planDeliverDate",
    valueType: "date-picker",
    colProps: { span: 6 },
    fieldProps: {
      type: "date",
      placeholder: "请选择计划发货日",
      valueFormat: "YYYY-MM-DD",
      clearable: true
    }
  },
  {
    label: "收件人姓名",
    prop: "receiverName",
    valueType: "input",
    colProps: { span: 6 },
    fieldProps: { placeholder: "请输入收件人姓名", clearable: true }
  },
  {
    label: "收件人电话",
    prop: "receiverPhone",
    valueType: "input",
    colProps: { span: 6 },
    fieldProps: { placeholder: "请输入收件人电话", clearable: true }
  },
  {
    label: "企业名称",
    prop: "enterpriseName",
    valueType: "input",
    colProps: { span: 6 },
    fieldProps: { placeholder: "请输入企业名称", clearable: true }
  },
  {
    label: "单据创建时间",
    prop: "createdAt",
    valueType: "date-picker",
    labelWidth: 110,
    colProps: { span: 8 },
    fieldProps: {
      type: "datetimerange",
      startPlaceholder: "开始时间",
      endPlaceholder: "结束时间",
      rangeSeparator: "至",
      valueFormat: "YYYY-MM-DD HH:mm:ss",
      clearable: true,
      popperClass: "picker-no-footer"
    }
  }
];

export const tableColumns = [
  { label: "确认单编号", prop: "code", minWidth: 180 },
  { label: "来源编号", prop: "mallOrderId", minWidth: 160 },
  { label: "企业名称", prop: "enterpriseName", minWidth: 160 },
  { label: "下单数量", prop: "orderQtyDesc", minWidth: 140 },
  { label: "计划发货日", prop: "planDeliverDate", minWidth: 140 },
  { label: "实际发货数量", prop: "deliverQtyDesc", minWidth: 140 },
  {
    label: "收件人信息",
    prop: "receiverName",
    minWidth: 200,
    formatter: (row: Record<string, any>) =>
      [row.receiverName, row.receiverPhone].filter(Boolean).join(" / ") || "-"
  },
  { label: "收货地址", prop: "receiverAddress", minWidth: 200, align: "left" },
  { label: "创建时间", prop: "createTime", minWidth: 180 },
  { label: "确认完成时间", prop: "confirmTime", minWidth: 180 },
  { label: "单据状态", prop: "status", slot: "status", minWidth: 120 },
  { label: "操作", prop: "action", slot: "action", width: 220, fixed: "right" }
];

export const STATUS_TAG_MAP: Record<
  string,
  "success" | "warning" | "info" | "danger"
> = {
  PENDING: "warning",
  CONFIRMED: "success",
  CANCELED: "info"
};
