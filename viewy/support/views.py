from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse
from .forms import BaseInquiryForm, NormalInquiryForm, CorporateInquiryForm
from django.shortcuts import redirect
from django.db import transaction
from django.core.mail import EmailMessage
from .models import NormalInquiry, CorporateInquiry

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

    def send_inquiry_notification(self, inquiry_instance):
        # メールの件名を設定
        subject = f'{inquiry_instance.name}様からのお問い合わせ'

        # メッセージの本文を組み立てる
        message_parts = [
            '以下の内容でお問い合わせがありました。',
            '--------------------------------',
            f'お問い合わせ種類: {"一般" if inquiry_instance.inquiry_type == "normal" else "法人"}',
            f'氏名: {inquiry_instance.name}様',
            f'メールアドレス: {inquiry_instance.email}',
            f'件名: {inquiry_instance.subject}',
            f'内容:',
            f'{inquiry_instance.content}',
            '--------------------------------',
        ]

        # NormalInquiry の場合の追加情報
        if isinstance(inquiry_instance, NormalInquiry):
            message_parts.extend([
                '追加情報:',
                f'発生日時: {inquiry_instance.occurrence_date.strftime("%Y-%m-%d %H:%M")}',
                f'発生URL: {inquiry_instance.occurrence_url}',
                f'機種: {inquiry_instance.device}',
                f'ブラウザ: {inquiry_instance.browser}',
            ])

        # CorporateInquiry の場合の追加情報
        elif isinstance(inquiry_instance, CorporateInquiry):
            message_parts.extend([
                '追加情報:',
                f'会社名: {inquiry_instance.company_name}様',
                f'所属部署名: {inquiry_instance.department_name if inquiry_instance.department_name else "情報なし"}',
            ])

        # メッセージ本文を改行で結合
        message = "\n".join(message_parts)

        # メールの送信者
        from_email = 'お問い合わせ <inquiry@viewy.net>'

        # メールの受信者
        recipient_list = ['support@viewy.net']


        # EmailMessage オブジェクトの作成
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            headers={'Reply-To': inquiry_instance.email}  # Reply-To ヘッダを追加
        )

        # メールの送信
        try:
            email.send()
            print("メールが正常に送信されました。")
        except Exception as e:
            print(f"メール送信中にエラーが発生しました: {e}")

    def send_confirmation_email(self, inquiry_instance):
        subject = 'お問い合わせありがとうございます'
        # メッセージの本文を組み立てる
        message_parts = [
            f"{inquiry_instance.name}様\n\n",
            "このたびは、お問い合わせいただきありがとうございます。\n",
            "弊社営業時間内に、いただきましたお問い合わせをご確認いたします。\n",
            "※お問い合わせの内容によっては、回答に時間がかかる場合や回答できない場合があります。\n\n\n",
            "[お問合せ内容]\n\n",
            f"■お名前\n{inquiry_instance.name}\n",
            f"■メールアドレス\n{inquiry_instance.email}\n",
            f"■件名\n{inquiry_instance.subject}\n",
            f"■お問い合わせ内容\n{inquiry_instance.content}\n",
        ]

        # NormalInquiry の場合の追加情報
        if isinstance(inquiry_instance, NormalInquiry):
            message_parts.extend([
                f"■発生日時: {inquiry_instance.occurrence_date.strftime('%Y-%m-%d %H:%M')}\n",
                f"■発生URL: {inquiry_instance.occurrence_url}\n",
                f"■機種: {inquiry_instance.device}\n",
                f"■ブラウザ: {inquiry_instance.browser}\n\n",
            ])

        # CorporateInquiry の場合の追加情報
        elif isinstance(inquiry_instance, CorporateInquiry):
            message_parts.extend([
                f"■会社名: {inquiry_instance.company_name}\n",
                f"■所属部署名: {inquiry_instance.department_name if inquiry_instance.department_name else '情報なし'}\n\n",
            ])

        # 追加のフッター情報
        message_parts.append(
            "------------------------------\n"
            "Viewy：https://www.viewy.net\n"
            "MAIL：support@viewy.net\n"
            "運営：合同会社Front&Front\n"
            "※営業時間：10:00～18:00 （土日・祝日は除く）\n"
            "Front&Front ホームページ：http://front-front.com/\n"
            "------------------------------\n\n"
            "このメールは送信専用のメールアドレスから送信されているため、返信できません。\n"
            "このメールに心当たりがない場合や、ご不明な点がございましたら、\n"
            "support@viewy.net までご連絡ください。"
        )

        # メッセージ本文を改行で結合
        message = "".join(message_parts)
        from_email = 'Viewyお問い合わせ <inquiry-conf@viewy.net>'
        recipient_list = [inquiry_instance.email]

        # EmailMessage オブジェクトの作成
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list
        )

        # メールの送信
        try:
            email.send()
            print("お客様へ確認メールが正常に送信されました。")
        except Exception as e:
            print(f"確認メール送信中にエラーが発生しました: {e}")

    def post(self, request, *args, **kwargs):
        base_form = BaseInquiryForm(request.POST)
        normal_form = NormalInquiryForm(request.POST)
        corporate_form = CorporateInquiryForm(request.POST)

        if base_form.is_valid():
            inquiry_type = base_form.cleaned_data['inquiry_type']

            # トランザクションを使用してデータの整合性を保証
            with transaction.atomic():
                if inquiry_type == 'normal':
                    if normal_form.is_valid():
                        normal_inquiry = normal_form.save(commit=False)
                        normal_inquiry.name = base_form.cleaned_data['name']
                        normal_inquiry.email = base_form.cleaned_data['email']
                        normal_inquiry.inquiry_type = inquiry_type
                        normal_inquiry.subject = normal_form.cleaned_data['normal_subject']
                        normal_inquiry.content = normal_form.cleaned_data['normal_content']
                        normal_inquiry.save()
                        self.send_inquiry_notification(normal_inquiry)
                        self.send_confirmation_email(normal_inquiry)
                        return redirect('support:inquiry_success')
                    else:
                        # 通常の問い合わせフォームのバリデーションエラーを表示
                        print("Normal Inquiry Form Errors:", normal_form.errors)

                elif inquiry_type == 'corporate':
                    if corporate_form.is_valid():
                        corporate_inquiry = corporate_form.save(commit=False)
                        corporate_inquiry.name = base_form.cleaned_data['name']
                        corporate_inquiry.email = base_form.cleaned_data['email']
                        corporate_inquiry.inquiry_type = inquiry_type
                        corporate_inquiry.subject = corporate_form.cleaned_data['corporate_subject']
                        corporate_inquiry.content = corporate_form.cleaned_data['corporate_content']
                        corporate_inquiry.save()
                        self.send_inquiry_notification(corporate_inquiry)
                        self.send_confirmation_email(corporate_inquiry)
                        return redirect('support:inquiry_success')
                    else:
                        # 法人問い合わせフォームのバリデーションエラーを表示
                        print("Corporate Inquiry Form Errors:", corporate_form.errors)

        else:
            # ベースフォームのバリデーションエラーを表示
            print("Base Inquiry Form Errors:", base_form.errors)

        # バリデーションに失敗した場合、フォームを再度表示
        return render(request, 'support/inquiry_form.html', {
            'base_form': base_form,
            'normal_form': normal_form,
            'corporate_form': corporate_form,
        })

class InquirySuccessView(TemplateView):
    template_name = 'support/inquiry_success.html'
