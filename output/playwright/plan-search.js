async (page) => {
  const input = page.getByRole('searchbox', {name:'搜索编号/名称'});
  for (const keyword of ['PLAN-A', 'PLAN-B']) {
    const request = page.waitForRequest(req => req.url().includes('/production/plans?') && req.url().includes('search='+keyword));
    await input.fill(keyword);
    await input.press('Enter');
    await request;
  }
}