function calculateCPM(targetViews, baseCPM) {
  if (targetViews < 200000) { // 10万回以上20万回未満の場合もそのままの値を返す
    return baseCPM;
  } else { // 20万回以上の場合は基本のCPMから100を引いた値を返す
    return baseCPM - 100;
  }
}

function calculateCPC(targetClicks, baseCPC) {
  if (targetClicks <= 2000) { // 2000以下の場合は基本のCPCをそのまま返す
    return baseCPC;
  } else { // 2000を超える場合は基本のCPCから10を引いた値を返す
    return baseCPC - 10;
  }
}

document.addEventListener('DOMContentLoaded', function () {
  let targetViewsInput = document.querySelector('#id_target_views');
  let targetClicksInput = document.querySelector('#id_target_clicks');
  let pricingModelRadios = document.querySelectorAll('[name="pricing_model"]');
  let cpmContainer = document.getElementById('cpm-container');
  let cpcContainer = document.getElementById('cpc-container');

  // 今月のCPMをページから直接取得します
  let baseCPMElement = document.querySelector('.cpm');
  // let baseCPM = parseFloat(baseCPMElement.textContent.replace('円', ''));
  let baseCPCElement = document.querySelector('.cpc');
  // let baseCPC = parseFloat(baseCPCElement.textContent.replace('円', ''));

  let nextbaseCPMElement = document.querySelector('.next-cpm');
  // let nextbaseCPM = parseFloat(nextbaseCPMElement.textContent.replace('円', ''));
  let nextbaseCPCElement = document.querySelector('.next-cpc');
  // let nextbaseCPC = parseFloat(nextbaseCPCElement.textContent.replace('円', ''));
  // console.log(nextbaseCPM);
  // console.log(nextbaseCPC);


  function updateDisplay() {

    let currentDate = new Date();
    let startDateInput = document.querySelector('#start-date-input');
    let selectedStartDate = new Date(startDateInput.value);
  
    // 次の月を取得するために現在の月に1を加える（月は0から始まるため）
    let nextMonth = currentDate.getMonth() + 1;
  
    // 現在が年の終わりの場合、来年の1月に調整する
    if (nextMonth > 11) {
      nextMonth = 0; // 1月は0で表される
      currentDate.setFullYear(currentDate.getFullYear() + 1);
    }
  
    // 使用するCPMとCPCを決定する
    let useNextMonthValues = selectedStartDate.getMonth() === nextMonth && selectedStartDate.getFullYear() === currentDate.getFullYear();
  
    let baseCPM = useNextMonthValues ? parseFloat(nextbaseCPMElement.textContent.replace('円', '')) : parseFloat(baseCPMElement.textContent.replace('円', ''));
    let baseCPC = useNextMonthValues ? parseFloat(nextbaseCPCElement.textContent.replace('円', '')) : parseFloat(baseCPCElement.textContent.replace('円', ''));

    let selectedPricingModel = document.querySelector('[name="pricing_model"]:checked').value;

    if (selectedPricingModel === 'CPM') {
      let targetViews = parseInt(targetViewsInput.value);
      cpmContainer.style.display = 'block';
      cpcContainer.style.display = 'none';
      let adjustedCPM = calculateCPM(targetViews, baseCPM);
      let budget = (targetViews / 1000) * adjustedCPM;

      if (targetViewsInput.value === '' || isNaN(targetViewsInput.value)) {
        document.querySelector('#calculated_cpm').textContent = '---';
        document.querySelector('#calculated_budget_cpm').textContent = '---';
        return; // 以降の処理を中断する
      }
      // CPMと見積金額を表示する場所を指定してください
      document.querySelector('#calculated_cpm').textContent = adjustedCPM.toLocaleString() + '円';
      document.querySelector('#calculated_budget_cpm').textContent = budget.toLocaleString() + '円';
    } else {
      let targetClicks = parseInt(targetClicksInput.value);
      cpmContainer.style.display = 'none';
      cpcContainer.style.display = 'block';
      let adjustedCPC = calculateCPC(targetClicks, baseCPC);
      let budget = targetClicks * adjustedCPC;

      if (targetClicksInput.value === '' || isNaN(targetClicksInput.value)) {
        document.querySelector('#calculated_cpc').textContent = '---';
        document.querySelector('#calculated_budget_cpc').textContent = '---';
        return; // 以降の処理を中断する
      }
      // CPCを表示する場所を指定してください
      document.querySelector('#calculated_cpc').textContent = adjustedCPC.toLocaleString() + '円';
      document.querySelector('#calculated_budget_cpc').textContent = budget.toLocaleString() + '円';
    }
  }

  let startDateInput = document.querySelector('#start-date-input');
  startDateInput.addEventListener('change', updateDisplay);

  targetViewsInput.addEventListener('input', updateDisplay);
  targetClicksInput.addEventListener('input', updateDisplay);

  pricingModelRadios.forEach(radio => {
    radio.addEventListener('change', updateDisplay);
  });

  // 初期表示の更新
  updateDisplay();
});