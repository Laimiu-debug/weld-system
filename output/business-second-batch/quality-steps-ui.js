async(page)=>{
 await page.getByRole('textbox',{name:'* 项目名称',exact:true}).fill('F07页面步骤回归');
 await page.getByRole('textbox',{name:'* 容器号',exact:true}).fill('V-F07-2');
 await page.getByRole('textbox',{name:'* 焊缝编号',exact:true}).fill('W-F07-2');
 await page.getByRole('combobox',{name:'质量标准',exact:true}).click();
}
