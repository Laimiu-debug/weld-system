import React from 'react'

export interface ListPageHeaderProps {
  title: string
  description?: React.ReactNode
  extra?: React.ReactNode
  icon?: React.ReactNode
}

/**
 * 业务列表页统一页头：标题字号、间距、副标题风格一致。
 * Layout Content 已有 padding，本组件不再叠加外边距以外的留白。
 */
const ListPageHeader: React.FC<ListPageHeaderProps> = ({
  title,
  description,
  extra,
  icon,
}) => {
  return (
    <div className="list-page-header">
      <div className="list-page-header-main">
        <h1 className="list-page-header-title">
          {icon ? <span className="list-page-header-icon">{icon}</span> : null}
          {title}
        </h1>
        {description ? (
          <p className="list-page-header-desc">{description}</p>
        ) : null}
      </div>
      {extra ? <div className="list-page-header-extra">{extra}</div> : null}
    </div>
  )
}

export default ListPageHeader
