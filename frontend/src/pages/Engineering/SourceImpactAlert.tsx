import { Alert, Button, List } from "antd";
import { Link } from "react-router-dom";

export interface SourceImpact {
  stale: boolean;
  issues: {
    source_type: string;
    source_id?: string | number;
    joint_ids: string[];
    message: string;
  }[];
  affected_joint_ids: string[];
  notice: string;
}

export default function SourceImpactAlert({
  impact,
  revisionId,
}: {
  impact?: SourceImpact;
  revisionId?: string;
}) {
  if (!impact?.stale) return null;
  return (
    <Alert
      type="warning"
      showIcon
      message="来源已变化，请核对受影响焊缝"
      description={
        <>
          <List
            size="small"
            dataSource={impact.issues}
            renderItem={(item) => (
              <List.Item>
                {item.message} · 影响 {item.joint_ids.length} 条焊缝
                {revisionId &&
                  item.joint_ids.map((id) => (
                    <Link
                      key={id}
                      to={`/engineering/revisions/${revisionId}/review?joint=${encodeURIComponent(id)}`}
                    >
                      <Button type="link">定位焊缝</Button>
                    </Link>
                  ))}
              </List.Item>
            )}
          />
          {impact.notice}
        </>
      }
    />
  );
}
