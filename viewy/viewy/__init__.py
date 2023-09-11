from .celery import app as celery_app

__all__ = ('celery_app',)

# このコードは、プロジェクトの__init__.pyファイルに追加することで、Djangoプロジェクトが起動する際にCeleryの設定を自動的に読み込むようにしています。

# from .celery import app as celery_app は、プロジェクトのルートディレクトリにあるcelery.pyからCeleryのインスタンスをインポートします。
# __all__ = ('celery_app',) は、このモジュールから何をインポートするかを指定するもので、Celeryのインスタンスのみをインポートするようにしています。

# これにより、Djangoプロジェクトが起動する際にCeleryも適切に初期化されます。