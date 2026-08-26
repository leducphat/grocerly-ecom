import hashlib
import hmac
import urllib.parse

class vnpay:
    def __init__(self):
        self.requestData = {}
        self.responseData = {}

    def get_payment_url(self, vnpay_payment_url, secret_key):
        inputData = sorted(self.requestData.items())
        queryString = ''
        seq = 0
        for key, val in inputData:
            if str(val).strip() == '':
                continue
            if seq == 1:
                queryString = queryString + "&" + key + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                queryString = key + '=' + urllib.parse.quote_plus(str(val))

        hashValue = self.__hmacsha512(secret_key.strip(), queryString)
        return vnpay_payment_url.strip() + "?" + queryString + '&vnp_SecureHash=' + hashValue

    def validate_response(self, secret_key):
        # Làm việc trên BẢN SAO. Trước đây hàm này `pop` thẳng vào `self.responseData`,
        # nên nó có tác dụng phụ: gọi lần thứ hai trên cùng một object luôn trả False vì
        # chữ ký đã bị lấy ra khỏi dữ liệu. `vnpay_return` và `vnpay_ipn` mỗi lần đều tạo
        # object mới nên chưa ai trúng bẫy này, nhưng một hàm kiểm chữ ký thì không có lý
        # do gì để sửa dữ liệu đầu vào của chính nó.
        received = dict(self.responseData)
        vnp_SecureHash = received.pop('vnp_SecureHash', None)
        # vnp_SecureHashType đi kèm chữ ký nhưng không nằm trong chuỗi được ký.
        received.pop('vnp_SecureHashType', None)

        inputData = sorted(received.items())
        hasData = ''
        seq = 0
        for key, val in inputData:
            if str(key).startswith('vnp_'):
                if str(val).strip() == '':
                    continue
                if seq == 1:
                    hasData = hasData + "&" + str(key) + '=' + urllib.parse.quote_plus(str(val))
                else:
                    seq = 1
                    hasData = str(key) + '=' + urllib.parse.quote_plus(str(val))
                    
        hashValue = self.__hmacsha512(secret_key.strip(), hasData)

        if not vnp_SecureHash:
            return False

        # So sánh KHÔNG phân biệt hoa thường. `hexdigest()` luôn trả chữ thường, và cổng
        # sandbox đang dùng cũng trả chữ thường — nên hiện tại không có gì hỏng. Nhưng
        # đặc tả VNPay không cam kết chữ thường, nên đây là rủi ro của lúc **chuyển sang
        # cổng thật**: nếu cổng trả chữ HOA thì mọi giao dịch THÀNH CÔNG đều bị coi là
        # sai chữ ký và rơi vào `payment-failed` — hỏng im lặng, không log nào chỉ ra
        # nguyên nhân, và chỉ lộ ra khi có người thật mất tiền mà đơn không được ghi nhận.
        #
        # `compare_digest` thay cho `==`: so khớp MAC phải dùng so sánh thời gian hằng số
        # để không rò rỉ thông tin qua thời gian phản hồi.
        return hmac.compare_digest(str(vnp_SecureHash).lower(), hashValue.lower())

    @staticmethod
    def __hmacsha512(key, data):
        byteKey = key.encode('utf-8')
        byteData = data.encode('utf-8')
        return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()
