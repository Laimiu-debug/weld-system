"""Explain source drift without altering approved or released snapshots."""
from app.models.engineering import ProductRevision
from app.models.matching import WPSMatchFreeze, WPSMatchRun
from app.models.pqr import PQR
from app.models.qualification import QualificationRulePack
from app.models.wps import WPS
from app.services.qualification_service import _record_snapshot, _hash


def rule_baseline(db, frozen):
    rule = frozen.get("rule") or {}
    pack_id = rule.get("rule_pack_id")
    pack = (
        db.query(QualificationRulePack)
        .filter(QualificationRulePack.id == pack_id)
        .first()
        if pack_id
        else None
    )
    return _record_snapshot(pack) if pack else None


def source_impact(db, sequence):
    issues = []
    sources = sequence.source_match_snapshot or []
    joint_ids = [item["joint_id"] for item in sources]

    def add(kind, identity, joints, message):
        issues.append(
            {
                "source_type": kind,
                "source_id": identity,
                "joint_ids": joints,
                "message": message,
            }
        )

    revision = (
        db.query(ProductRevision)
        .filter(ProductRevision.id == sequence.product_revision_id)
        .first()
    )
    if (
        not revision
        or revision.data_version != sequence.source_data_version
        or revision.status != "approved"
    ):
        add("drawing", sequence.product_revision_id, joint_ids, "来源图纸数据或审核状态已变化")
    if revision:
        newer = (
            db.query(ProductRevision)
            .filter(
                ProductRevision.product_id == revision.product_id,
                ProductRevision.revision_number > revision.revision_number,
            )
            .first()
        )
        if newer:
            add("drawing_revision", newer.id, joint_ids, "该产品已有更新图纸版本，请核对影响")
    cache = {}
    for source in sources:
        joint = source["joint_id"]
        frozen = source.get("snapshot") or {}
        for kind, model in (("wps", WPS), ("pqr", PQR)):
            saved = frozen.get(kind) or {}
            identity = saved.get("id")
            if identity is None:
                add(kind, None, [joint], f"冻结快照缺少 {kind.upper()} 来源标识")
                continue
            key = (kind, identity)
            if key not in cache:
                row = db.query(model).filter(model.id == identity).first()
                cache[key] = _record_snapshot(row) if row else None
            current = cache[key]
            if current is None or any(current.get(k) != v for k, v in saved.items()):
                add(kind, identity, [joint], f"{kind.upper()} 已变化或删除，历史任务仍保存原冻结快照")
        rule = frozen.get("rule") or {}
        pack_id = rule.get("rule_pack_id")
        if pack_id:
            pack = (
                db.query(QualificationRulePack)
                .filter(QualificationRulePack.id == pack_id)
                .first()
            )
            baseline = source.get("rule_baseline")
            if (
                not pack
                or pack.status != "published"
                or str(pack.version) != str(rule.get("rule_pack_version"))
                or (baseline and _hash(_record_snapshot(pack)) != _hash(baseline))
            ):
                add("rule_pack", pack_id, [joint], "资格规则包内容、版本或发布状态已变化")
        latest = (
            db.query(WPSMatchFreeze)
            .join(WPSMatchRun, WPSMatchRun.id == WPSMatchFreeze.run_id)
            .filter(
                WPSMatchFreeze.revision_id == sequence.product_revision_id,
                WPSMatchFreeze.weld_joint_id == joint,
                WPSMatchRun.status == "approved",
            )
            .order_by(WPSMatchFreeze.frozen_at.desc())
            .first()
        )
        run = (
            db.query(WPSMatchRun).filter(WPSMatchRun.id == latest.run_id).first()
            if latest
            else None
        )
        if revision and run and run.source_data_version != revision.data_version:
            add(
                "match_source",
                getattr(latest, "id", None),
                [joint],
                "匹配计算所依据的图纸数据版本已过期",
            )
        if (
            not latest
            or latest.id != source.get("id")
            or _hash(latest.frozen_snapshot) != _hash(frozen)
        ):
            add("match_freeze", source.get("id"), [joint], "已批准匹配冻结版本已变化或失效")
    return {
        "stale": bool(issues),
        "issues": issues,
        "affected_joint_ids": sorted(
            {joint for issue in issues for joint in issue["joint_ids"]}
        ),
        "notice": "来源变化不改写历史发布批次；调整施工方案须按生产变更流程处理。",
    }
