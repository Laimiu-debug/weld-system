import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
} from "antd";

const methods = ["VT", "RT", "UT", "MT", "PT", "ET", "LT", "AT"].map(
  (value) => ({ value, label: value }),
);

export default function TreatmentPlanEditor() {
  return (
    <>
      <Alert
        type="info"
        message="按实际批准工艺添加热处理阶段。整体处理使用共同批组编号；各焊缝的同批组参数必须一致。检测方法须覆盖上方已规定的检测要求。"
      />
      <Form.List name="treatment_plan">
        {(fields, { add, remove }) => (
          <>
            {fields.map((field) => (
              <Card
                key={field.key}
                size="small"
                title={`热处理阶段 ${field.name + 1}`}
                extra={
                  <Button onClick={() => remove(field.name)}>删除阶段</Button>
                }
              >
                <Form.Item
                  name={[field.name, "code"]}
                  label="阶段编号"
                  rules={[
                    { required: true },
                    {
                      pattern: /^[A-Za-z0-9_-]{1,30}$/,
                      message: "使用字母、数字、横线或下划线",
                    },
                  ]}
                >
                  <Input />
                </Form.Item>
                <Form.Item
                  name={[field.name, "scope"]}
                  label="处理范围"
                  rules={[{ required: true }]}
                >
                  <Select
                    options={[
                      { value: "local", label: "局部" },
                      { value: "global", label: "整体" },
                    ]}
                  />
                </Form.Item>
                <Form.Item
                  name={[field.name, "group"]}
                  label="整体处理批组编号（局部留空）"
                >
                  <Input maxLength={30} />
                </Form.Item>
                <Space wrap>
                  <Form.Item
                    name={[field.name, "temperature_min"]}
                    label="温度下限 ℃"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={2000} />
                  </Form.Item>
                  <Form.Item
                    name={[field.name, "temperature_max"]}
                    label="温度上限 ℃"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={2000} />
                  </Form.Item>
                  <Form.Item
                    name={[field.name, "hold_minutes"]}
                    label="保温时间 min"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0.1} max={100000} />
                  </Form.Item>
                </Space>
                <Form.Item
                  name={[field.name, "nde_before"]}
                  label="本阶段热处理前检测"
                >
                  <Select mode="multiple" options={methods} />
                </Form.Item>
                <Form.Item
                  name={[field.name, "nde_after"]}
                  label="本阶段热处理后检测"
                >
                  <Select mode="multiple" options={methods} />
                </Form.Item>
              </Card>
            ))}
            <Button
              disabled={fields.length >= 12}
              onClick={() =>
                add({
                  code: `H${fields.length + 1}`,
                  scope: "local",
                  nde_before: [],
                  nde_after: [],
                })
              }
            >
              添加热处理阶段
            </Button>
          </>
        )}
      </Form.List>
    </>
  );
}
