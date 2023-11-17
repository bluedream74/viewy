function calculateCPM(targetViews, baseCPM, isDiscounted = null) {
  let adjustedCPM = baseCPM;

  if (targetViews >= 200000) {
    adjustedCPM -= 100;
  }

  if (isDiscounted) {
    adjustedCPM *= 0.9;
  }
  return Math.round(adjustedCPM); // 整数に丸める
}

function calculateCPC(targetClicks, baseCPC, isDiscounted = false) {
  let adjustedCPC = baseCPC;

  if (targetClicks >= 2000) {
    adjustedCPC -= 10;
  }

  if (isDiscounted) {
    adjustedCPC *= 0.9;
  }
  return Math.round(adjustedCPC); // 整数に丸める
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

  // data-original属性を持つ要素を選択
  var elementWithDataOriginal = document.querySelector('[data-original]');

  // 属性の値を取得（属性が存在しない場合はnullが返される）
  var dataOriginalValue = elementWithDataOriginal ? elementWithDataOriginal.getAttribute('data-original') : null;

  // 初回限定キャンペーンチェックボックスの参照
  const firstTimeCampaignCheckbox = document.getElementById('first-time-campaign-checkbox');

  function handleFirstTimeCampaignChange() {
    if (firstTimeCampaignCheckbox.checked) {
      // 初回限定料金の処理
      const fixedCPM = 0;
      const budget = 0;

      document.querySelector('#id_pricing_model').value = 'CPM';
      document.querySelector('#id_target_views').value = 100000;
      document.querySelector('#calculated_cpm').textContent = `${fixedCPM.toLocaleString()}円`;
      document.querySelector('#calculated_budget_cpm').textContent = `${budget.toLocaleString()}円`;

      // 初回限定料金のテキストを表示
      const calculatedCPMElement = document.querySelector('.checkbox-container');
      calculatedCPMElement.insertAdjacentHTML('afterend', '<p id="discount-note" style="color: red; class="info-description">※初回限定価格として目標表示回数100,000回、<br>　CPM式、見積金額0円のご案内となります。</p>');
      // フォーム要素を読み取り専用に設定
      targetViewsInput.readOnly = true;
      targetClicksInput.readOnly = true;
      // pricingModelRadios.forEach(radio => radio.disabled = true);
    } else {
      // 初回限定料金のテキストを削除
      const discountNote = document.getElementById('discount-note');
      if (discountNote) {
        discountNote.remove();
      }
      // フォーム要素の読み取り専用を解除
      targetViewsInput.readOnly = false;
      targetClicksInput.readOnly = false;
      // pricingModelRadios.forEach(radio => radio.disabled = false);
      // 表示を更新
      updateDisplay();
    }
  }

  // チェックボックスの変更イベントにリスナーを設定
  if (firstTimeCampaignCheckbox) {
    firstTimeCampaignCheckbox.addEventListener('change', handleFirstTimeCampaignChange);
  }

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
      let adjustedCPM = calculateCPM(targetViews, baseCPM, dataOriginalValue);
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
      let adjustedCPC = calculateCPC(targetClicks, baseCPC, dataOriginalValue);
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