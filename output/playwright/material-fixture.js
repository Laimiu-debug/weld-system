async (page) => {
  const ws = {id:'personal_901', type:'personal', name:'功能测试工作区', membership_tier:'personal_pro', quota_info:{}};
  const user = {id:901, username:'功能测试', email:'fixture@example.test', is_admin:true, is_active:true, membership_type:'personal', membership_tier:'personal_pro'};
  let material = null;
  let transactions = [];
  await page.unroute('**/api/v1/**');
  await page.route('**/api/v1/**', async route => {
    const req = route.request(); const path = req.url().split('?')[0].replace(/^https?:\/\/[^/]+/, ''); const url = {searchParams: new Map((req.url().split('?')[1] || '').split('&').map(v => v.split('=')))};
    let body = {success:true,data:{items:[],total:0}};
    if(path.includes('/materials')) {
      if(path.includes('//')) throw new Error('Double slash in material URL');
      if(url.searchParams.get('workspace_type') !== 'personal') throw new Error('Missing workspace');
      if(path.endsWith('/stock-in') || path.endsWith('/stock-out')) {
        const quantity = Number(url.searchParams.get('quantity'));
        const before = material.current_stock;
        material.current_stock += path.endsWith('/stock-in') ? quantity : -quantity;
        transactions.push({id:transactions.length+1,transaction_number:'FIXTURE-'+(transactions.length+1), transaction_type:path.endsWith('/stock-in')?'in':'out', quantity, unit:'kg', stock_before:before, stock_after:material.current_stock, transaction_date:'2026-09-05T08:00:00', created_at:'2026-09-05T08:00:00'});
        body={success:true,data:{current_stock:material.current_stock}};
      } else if(path.endsWith('/transactions')) body={success:true,data:{items:transactions,total:transactions.length}};
      else if(req.method()==='POST') {
        const data=req.postDataJSON();
        if(!data.material_code || data.current_stock!==12 || data.currency!=='CNY') throw new Error('Incomplete creation payload');
        material={...data,id:42,workspace_type:'personal',user_id:901,created_at:'2026-09-05T08:00:00'};
        body={success:true,data:material};
      } else if(req.method()==='PUT') {
        const data=req.postDataJSON();
        if('current_stock' in data || 'unit' in data) throw new Error('Edit overwrites inventory');
        material={...material,...data}; body={success:true,data:material};
      } else if(req.method()==='DELETE') {material=null;body={success:true};}
      else if(path.endsWith('/42')) body={success:true,data:material};
      else body={success:true,data:{items:material?[material]:[],total:material?1:0}};
    } else if(path.endsWith('/workspace/workspaces')) body=[ws];
    else if(path.includes('/workspace/workspaces/')) body=ws;
    else if(path.endsWith('/users/me')) body=user;
    else if(path.includes('/membership')) body={tier:'personal_pro',features:[],quotas:{}};
    await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(body)});
  });
  await page.evaluate(({ws,user})=>{
    localStorage.setItem('token','isolated-ui-fixture');
    localStorage.setItem('user',JSON.stringify(user));
    localStorage.setItem('auth-storage',JSON.stringify({state:{user,isAuthenticated:true},version:0}));
    localStorage.setItem('current_workspace',JSON.stringify(ws));
  },{ws,user});
  await page.goto('http://127.0.0.1:5187/materials/create');
}