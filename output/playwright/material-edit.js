async (page) => {
  await page.getByRole('button', {name:'edit 编辑焊材'}).click();
  await page.getByRole('textbox', {name:'* 焊材名称',exact:true}).fill('焊材功能测试已修改');
  await page.getByRole('button', {name:'right 下一步'}).click();
  if(!await page.getByRole('spinbutton', {name:'* 当前库存',exact:true}).isDisabled()) throw new Error('Inventory should be readonly');
  await page.getByRole('button', {name:'right 下一步'}).click();
  await page.getByRole('button', {name:'right 下一步'}).click();
  await page.getByRole('button', {name:'save 保存修改'}).click();
  await page.getByText('焊材功能测试已修改',{exact:true}).waitFor();
}