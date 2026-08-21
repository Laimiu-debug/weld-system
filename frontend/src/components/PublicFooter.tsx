import React from 'react'
import { Link } from 'react-router-dom'

const PublicFooter: React.FC = () => (
  <footer className="public-footer">
    <div className="public-footer__inner">
      <div className="public-footer__grid">
        <div className="public-footer__brand">
          <strong>焊序</strong>
          <p>专业的焊接工艺管理平台，服务工艺、质量与现场协同。</p>
        </div>
        <div>
          <h5>产品</h5>
          <Link to="/features">产品功能</Link>
          <Link to="/analytics">统计分析</Link>
        </div>
        <div>
          <h5>支持</h5>
          <Link to="/about">关于我们</Link>
        </div>
        <div>
          <h5>法律</h5>
          <Link to="/privacy-policy">隐私政策</Link>
          <Link to="/terms-of-service">服务条款</Link>
        </div>
      </div>
      <div className="public-footer__copy">
        © {new Date().getFullYear()} 焊序. All rights reserved. | 鲁ICP备2025191429号-1
      </div>
    </div>
  </footer>
)

export default PublicFooter
