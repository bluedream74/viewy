from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse
from .forms import BaseInquiryForm, NormalInquiryForm, CorporateInquiryForm

class DynamicTemplateView(TemplateView):
    def get_template_names(self):
        pretitle = self.kwargs.get('pretitle')
        title = self.kwargs.get('title')
        subtitle = self.kwargs.get('subtitle')

        # 3つのパラメーターが指定された場合
        if pretitle and title and subtitle:
            return [f'support/{pretitle}/{title}/{subtitle}.html']

        # 2つのパラメーターが指定された場合
        if pretitle and title:
            return [f'support/{pretitle}/{title}/index.html']  # ここを変更

        # 1つのパラメーターが指定された場合
        if pretitle:
            return [f'support/{pretitle}/index.html']

        # パラメーターが指定されていない場合
        return ['support/first.html']


class InquiryFormView(View):
    def get(self, request, *args, **kwargs):
        base_form = BaseInquiryForm()
        normal_form = NormalInquiryForm()
        corporate_form = CorporateInquiryForm()
        return render(request, 'support/inquiry_form.html', {
            'base_form': base_form,
            'normal_form': normal_form,
            'corporate_form': corporate_form,
        })

    def post(self, request, *args, **kwargs):
        base_form = BaseInquiryForm(request.POST)
        normal_form = NormalInquiryForm(request.POST)
        corporate_form = CorporateInquiryForm(request.POST)

        if base_form.is_valid():
            inquiry_type = base_form.cleaned_data['inquiry_type']
            if inquiry_type == 'normal' and normal_form.is_valid():
              pass
                # 通常の問い合わせデータの処理
                # ...
            elif inquiry_type == 'corporate' and corporate_form.is_valid():
              pass
                # 法人の問い合わせデータの処理
                # ...

            # フォームの送信後の処理（成功画面へのリダイレクトなど）
            return redirect('success_page')

        return render(request, 'support/inquiry_form.html', {
            'base_form': base_form,
            'normal_form': normal_form,
            'corporate_form': corporate_form,
        })

