async (page) => {
  const pending = page.waitForEvent('download');
  await page.getByRole('button', {name:'download 导出信息'}).click();
  const download = await pending;
  await download.saveAs('output/playwright/material-export.csv');
  await page.screenshot({path:'output/playwright/material-detail.png', fullPage:true});
}