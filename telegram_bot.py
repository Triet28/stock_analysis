import logging
import datetime
from dotenv import load_dotenv
import os
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from settings import get_plot_settings, update_plot_settings, DEFAULT_PLOT_SETTINGS

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("telegram_bot.log")
    ]
)

logger = logging.getLogger(__name__)
load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hàm xử lý khi người dùng bắt đầu tương tác với bot"""
    # Tạo keyboard để hiển thị các lệnh có thể sử dụng
    keyboard = [
        [InlineKeyboardButton("Phân tích cổ phiếu", callback_data="help_predict")],
        [InlineKeyboardButton("Xem biểu đồ", callback_data="help_chart")],
        [InlineKeyboardButton("Cài đặt biểu đồ", callback_data="settings_plot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        f"👋 Xin chào {update.effective_user.first_name}!\n\n"
        f"Tôi là *Stock Analysis Bot*, trợ lý phân tích chứng khoán của bạn. "
        f"Tôi có thể giúp bạn phân tích cổ phiếu với các chỉ báo kỹ thuật và đưa ra khuyến nghị.\n\n"
        f"*Các lệnh cơ bản:*\n"
        f"• /predict [mã CK] [short/long] - Phân tích và đưa ra khuyến nghị\n"
        f"• /chart [mã CK] - Xem biểu đồ kỹ thuật\n"
        f"• /settings - Cài đặt các chỉ báo kỹ thuật\n"
        f"• /help - Xem hướng dẫn chi tiết\n\n"
        f"Bấm vào nút bên dưới để xem hướng dẫn chi tiết về từng lệnh:"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hàm hiển thị hướng dẫn sử dụng bot"""
    help_text = (
        "*🤖 HƯỚNG DẪN SỬ DỤNG BOT PHÂN TÍCH CHỨNG KHOÁN*\n\n"
        "*Các lệnh cơ bản:*\n\n"
        "1️⃣ */predict [mã CK] [short/long] [ngày]*\n"
        "   - Phân tích kỹ thuật và đưa ra khuyến nghị\n"
        "   - `short`: Phân tích ngắn hạn (20 ngày)\n"
        "   - `long`: Phân tích dài hạn (60 ngày)\n"
        "   - `ngày`: (Tùy chọn) Ngày kết thúc phân tích (YYYY-MM-DD). Nếu để trống sẽ lấy ngày hiện tại.\n"
        "   - Ví dụ: `/predict FPT short` hoặc `/predict FPT long 2025-08-05`\n\n"
        "2️⃣ */chart [mã CK]*\n"
        "   - Hiển thị biểu đồ kỹ thuật\n"
        "   - Có thể thêm khoảng thời gian: `/chart FPT 2023-01-01 2023-03-01`. Nếu để trống sẽ lấy khoảng thời gian mặc định (730 ngày kể từ ngày hiện tại)\n"
        "   - Ví dụ: `/chart VNM`\n\n"
        "3️⃣ */settings*\n"
        "   - Tùy chỉnh cài đặt biểu đồ và các chỉ báo kỹ thuật\n"
        "   - Có thể tùy chỉnh được các tham số như: MA, MACD, RSI, Dải Bollinger, Mây Ichimoku. Khi các tham số này được bật, nó sẽ được thêm vào biểu đồ.\n"
        "   - Có thể tùy chỉnh việc hiển thị các nến đặc biệt trên biểu đồ. Lưu ý chỉ có thể hiển thị một lúc 4 loại nến đặc biệt\n"
        "4️⃣ */help*\n"
        "   - Hiển thị hướng dẫn này\n\n"
        "*Các chỉ báo được sử dụng:*\n"
        "• RSI (Relative Strength Index)\n"
        "• MACD (Moving Average Convergence Divergence)\n"
        "• Bollinger Bands\n"
        "• Moving Averages\n"
        "• Nến Nhật (Candlestick Patterns)"
    )
    
    keyboard = [
        [InlineKeyboardButton("Phân tích cổ phiếu", callback_data="help_predict")],
        [InlineKeyboardButton("Xem biểu đồ", callback_data="help_chart")],
        [InlineKeyboardButton("Cài đặt", callback_data="help_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi người dùng nhấn vào các nút inline keyboard"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help_predict":
        help_text = (
            "*🔍 HƯỚNG DẪN LỆNH PREDICT*\n\n"
            "Cú pháp: `/predict [mã CK] [short/long] [ngày]`\n\n"
            "*Tham số:*\n"
            "• `[mã CK]`: Mã cổ phiếu cần phân tích (VD: FPT, VNM)\n"
            "• `[short/long]`: Khung thời gian phân tích\n"
            "  - `short`: Phân tích ngắn hạn (60 ngày)\n"
            "  - `long`: Phân tích dài hạn (180 ngày)\n"
            "• `[ngày]`: (Tùy chọn) Ngày kết thúc phân tích (YYYY-MM-DD)\n"
            "  - Nếu không điền, mặc định là ngày hiện tại\n\n"
            "*Ví dụ:*\n"
            "• `/predict FPT short` - Phân tích ngắn hạn mã FPT\n"
            "• `/predict VNM long` - Phân tích dài hạn mã VNM\n"
            "• `/predict FPT short 2025-08-05` - Phân tích mã FPT đến ngày 05/08/2025\n\n"
            "*Bot sẽ trả về:*\n"
            "• Khuyến nghị tổng hợp (BUY/SELL/HOLD)\n"
            "• Chi tiết phân tích từ các chỉ báo kỹ thuật\n"
            "• Các tín hiệu giao dịch và lý do"
        )
        await query.message.reply_text(help_text, parse_mode="Markdown")
    
    elif query.data == "help_chart":
        help_text = (
            "*📊 HƯỚNG DẪN LỆNH CHART*\n\n"
            "Cú pháp: `/chart [mã CK]`\n\n"
            "*Tham số:*\n"
            "• `[mã CK]`: Mã cổ phiếu cần xem biểu đồ (VD: FPT, VNM)\n\n"
            "*Ví dụ:*\n"
            "• `/chart FPT` - Xem biểu đồ kỹ thuật mã FPT\n\n"
            "*Bot sẽ trả về:*\n"
            "• Biểu đồ nến (Candlestick) với các chỉ báo kỹ thuật\n"
            "• Volume\n"
            "• Moving Averages\n"
            "• Bollinger Bands\n"
            "• RSI và MACD (nếu có)"
        )
        await query.message.reply_text(help_text, parse_mode="Markdown")
        
    elif query.data == "help_settings":
        help_text = (
            "*⚙️ HƯỚNG DẪN LỆNH SETTINGS*\n\n"
            "Cú pháp: `/settings`\n\n"
            "*Mô tả:*\n"
            "• Lệnh này cho phép bạn tùy chỉnh cài đặt cho các chỉ báo kỹ thuật sẽ hiển thị trên biểu đồ\n"
            "• Bật/tắt các chỉ báo: Moving Averages, Bollinger Bands, RSI, MACD, Ichimoku, Support & Resistance, v.v.\n"
            "• Cài đặt mẫu hình nến để đánh dấu trên biểu đồ\n\n"
            "*Các tính năng:*\n"
            "• Bật/tắt các chỉ báo kỹ thuật\n"
            "• Tùy chỉnh các mẫu hình nến muốn đánh dấu\n"
            "• Khôi phục cài đặt mặc định\n\n"
            "*Lưu ý:*\n"
            "• Cài đặt được lưu riêng cho từng người dùng\n"
            "• Khi sử dụng lệnh `/chart`, biểu đồ sẽ được tạo theo cài đặt của bạn"
        )
        await query.message.reply_text(help_text, parse_mode="Markdown")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hàm phân tích cổ phiếu và trả về khuyến nghị"""
    if not context.args:
        await update.message.reply_text(
            '⚠️ Vui lòng nhập mã chứng khoán và khung thời gian!\n'
            'Ví dụ: `/predict FPT short` hoặc `/predict FPT long 2025-08-05`',
            parse_mode="Markdown"
        )
        return
    
    # Kiểm tra có đủ ít nhất 2 tham số (symbol và range) không
    if len(context.args) < 2:
        await update.message.reply_text(
            '⚠️ Thiếu tham số khung thời gian (short/long)!\n'
            'Ví dụ đúng: `/predict FPT short` hoặc `/predict VNM long`',
            parse_mode="Markdown"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Kiểm tra tham số range
    if context.args[1].lower() not in ["short", "long"]:
        await update.message.reply_text(
            '⚠️ Tham số khung thời gian không hợp lệ. Chỉ chấp nhận `short` hoặc `long`.\n'
            'Ví dụ đúng: `/predict FPT short` hoặc `/predict VNM long`',
            parse_mode="Markdown"
        )
        return
    
    range_value = context.args[1].lower()
    
    # Mặc định sử dụng ngày hiện tại (đã định dạng)
    end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Kiểm tra nếu có tham số ngày cụ thể
    if len(context.args) > 2:
        try:
            # Lấy và xác thực định dạng ngày từ tham số
            date_param = context.args[2]
            datetime.datetime.strptime(date_param, '%Y-%m-%d')  # Kiểm tra định dạng hợp lệ
            end_date = date_param  # Nếu hợp lệ, sử dụng ngày từ tham số
        except ValueError:
            await update.message.reply_text(
                '⚠️ Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD.\n'
                'Ví dụ: `/predict FPT short 2025-08-05`',
                parse_mode="Markdown"
            )
            return
    
    # Hiển thị thông báo phù hợp dựa trên các tham số
    message_text = f'⏳ Đang phân tích mã *{symbol}* (khung thời gian: *{range_value}*, đến ngày: *{end_date}*)'
    
    # Thông báo đang xử lý
    processing_message = await update.message.reply_text(
        message_text,
        parse_mode="Markdown"
    )
    
    try:
        # Chuẩn bị dữ liệu gửi đến API
        request_data = {
            "symbol": symbol, 
            "range": range_value,
            "endDate": end_date  # Luôn có giá trị: hoặc là ngày được chỉ định, hoặc là ngày hiện tại đã định dạng
        }
            
        # Gọi API
        response = requests.post(
            f"{os.getenv('SERVER_URL')}/predict", 
            json=request_data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Tạo icon theo khuyến nghị
            recommendation_icon = "🟢" if result['final_statement'] == "BUY" else "🔴" if result['final_statement'] == "SELL" else "🟡"
            
            # Tạo phản hồi chi tiết
            message = f"*📊 PHÂN TÍCH MÃ {symbol}*\n"
            message += f"*Khung thời gian:* {range_value.upper()}\n"
            if 'startDate' in result and 'endDate' in result:
                message += f"*Dữ liệu:* {result['startDate']} - {result['endDate']}\n"
            message += f"*Khuyến nghị:* {recommendation_icon} *{result['final_statement']}*\n\n"
            
            # Hiển thị chi tiết từng chỉ báo
            message += "*💹 CHI TIẾT PHÂN TÍCH:*\n\n"
            
            # Định nghĩa icon cho từng loại chỉ báo
            indicator_icons = {
                "RSI": "📈",
                "Moving Averages": "📉",
                "MACD": "📊",
                "Bollinger Bands": "🔔",
                "Candlestick Patterns": "🕯️"
            }
            
            # Định nghĩa icon cho từng khuyến nghị
            signal_icons = {
                "BUY": "🟢",
                "SELL": "🔴",
                "HOLD": "🟡",
                "BULLISH": "🟢",
                "BEARISH": "🔴",
                "NEUTRAL": "🟡"
            }
            
            # Thêm phân tích chi tiết với định dạng đẹp hơn
            for indicator, analysis in result["analysis"].items():
                # Lấy icon cho loại chỉ báo, mặc định là 🔍 nếu không có
                icon = indicator_icons.get(indicator, "🔍")
                
                # Lấy icon cho khuyến nghị, mặc định là ⚪ nếu không có
                statement_icon = signal_icons.get(analysis['statement'], "⚪")
                
                # Tên chỉ báo và khuyến nghị
                message += f"{icon} *{indicator}*: {statement_icon} {analysis['statement']}\n"
                
                # Thêm chi tiết phân tích của từng chỉ báo
                if 'analysis' in analysis and analysis['analysis']:
                    for signal in analysis['analysis']:
                        if 'signal' in signal and 'reason' in signal and 'date' in signal:
                            # Lấy icon cho tín hiệu
                            signal_icon = signal_icons.get(signal['signal'], "⚪")
                            message += f"   • {signal['date']}: {signal_icon} {signal['signal']} - {signal['reason']}\n"
                
                # Thêm thông tin bổ sung nếu có
                if 'details' in analysis and analysis['details']:
                    message += f"   • *Chi tiết:* {analysis['details']}\n"
                
                message += "\n"
            
            # Thêm lưu ý/disclaimer
            message += "*Lưu ý:* Đây là phân tích kỹ thuật tự động, chỉ mang tính chất tham khảo."
            
            # Xóa thông báo đang xử lý
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=processing_message.message_id
            )
            
            # Gửi kết quả phân tích
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            # Xóa thông báo đang xử lý
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=processing_message.message_id
            )
            
            error_message = f"❌ Lỗi: {response.status_code}"
            try:
                error_detail = response.json().get("detail", response.text)
                error_message += f"\n{error_detail}"
            except:
                error_message += f"\n{response.text}"
                
            await update.message.reply_text(error_message)
    
    except Exception as e:
        logger.error(f"Error in predict command: {str(e)}", exc_info=True)
        # Xóa thông báo đang xử lý
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=processing_message.message_id
            )
        except:
            pass
            
        await update.message.reply_text(
            f"❌ Không thể kết nối tới API: {str(e)}\n"
            f"Vui lòng kiểm tra lại kết nối hoặc thử lại sau."
        )

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hàm xem biểu đồ kỹ thuật của mã chứng khoán"""
    if not context.args:
        await update.message.reply_text(
            '⚠️ Vui lòng nhập mã chứng khoán!\n'
            'Ví dụ: `/chart FPT`\n'
            'Hoặc với khoảng thời gian: `/chart FPT 2023-01-01 2023-03-01`',
            parse_mode="Markdown"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Thông báo đang xử lý
    processing_message = await update.message.reply_text(
        f'⏳ Đang tạo biểu đồ cho mã *{symbol}*...',
        parse_mode="Markdown"
    )
    
    try:
        # Khởi tạo các biến startDate và endDate (có thể để trống, API sẽ xử lý)
        start_date = None
        end_date = None
        
        # Kiểm tra nếu có tham số cho start_date
        if len(context.args) > 1:
            try:
                # Định dạng YYYY-MM-DD
                start_date = context.args[1]
                datetime.datetime.strptime(start_date, '%Y-%m-%d')  # Validate format
            except ValueError:
                await update.message.reply_text(
                    '⚠️ Định dạng ngày bắt đầu không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD.\n'
                    'Ví dụ: `/chart FPT 2023-01-01`',
                    parse_mode="Markdown"
                )
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=processing_message.message_id
                )
                return
                
        # Kiểm tra nếu có tham số cho end_date
        if len(context.args) > 2:
            try:
                # Định dạng YYYY-MM-DD
                end_date = context.args[2]
                datetime.datetime.strptime(end_date, '%Y-%m-%d')  # Validate format
            except ValueError:
                await update.message.reply_text(
                    '⚠️ Định dạng ngày kết thúc không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD.\n'
                    'Ví dụ: `/chart FPT 2023-01-01 2023-03-01`',
                    parse_mode="Markdown"
                )
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=processing_message.message_id
                )
                return
        
        # Lấy settings của người dùng
        user_id = update.effective_user.id
        plot_settings = get_plot_settings(user_id)
        
        # Chuẩn bị request data với settings của người dùng
        request_data = {
            "symbol": symbol,
            **plot_settings  # Trải rộng tất cả settings của người dùng
        }
        
        # Thêm startDate và endDate nếu được cung cấp
        if start_date:
            request_data["startDate"] = start_date
            
        if end_date:
            request_data["endDate"] = end_date
        
        # Gọi API
        response = requests.post(
            f"{os.getenv('SERVER_URL')}/plot", 
            json=request_data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Xóa thông báo đang xử lý
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=processing_message.message_id
            )
            
            # Gửi biểu đồ
            if "chart_url" in result:
                caption = f"📊 *Biểu đồ kỹ thuật {symbol}*\n"
                
                # Kiểm tra nhiều trường hợp khác nhau về key trong response
                if "startDate" in result and "endDate" in result:
                    # Định dạng ngày từ YYYY-MM-DD sang DD/MM/YYYY cho hiển thị
                    try:
                        start_display = datetime.datetime.strptime(result['startDate'], '%Y-%m-%d').strftime('%d/%m/%Y')
                        end_display = datetime.datetime.strptime(result['endDate'], '%Y-%m-%d').strftime('%d/%m/%Y')
                        caption += f"(Dữ liệu từ {start_display} đến {end_display})"
                    except (ValueError, KeyError):
                        # Nếu định dạng ngày không hợp lệ, hiển thị nguyên bản
                        caption += f"(Dữ liệu từ {result['startDate']} đến {result['endDate']})"
                # Fallback cho khoảng thời gian mặc định nếu không có trong response
                else:
                    default_end_date = datetime.datetime.now().strftime('%d/%m/%Y')
                    default_start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%d/%m/%Y')
                    caption += f"(Dữ liệu từ {default_start_date} đến {default_end_date}, ước tính)"
                
                await update.message.reply_photo(
                    photo=result["chart_url"],
                    caption=caption,
                    parse_mode="Markdown"
                )
                
                # Kiểm tra các thông tin bổ sung cần hiển thị
                additional_info_sent = False
                
                # 1. Phân tích Candle Patterns nếu CP được bật trong settings
                if "candle_patterns" in result and plot_settings.get("CP", False):
                    additional_info_sent = True
                    patterns_message = "*🕯️ PHÂN TÍCH MẪU HÌNH NẾN:*\n\n"
                    
                    # Lấy các patterns từ API response
                    candle_patterns = result["candle_patterns"]
                    
                    # Hiển thị thống kê
                    if "candle_analysis" in candle_patterns:
                        stats = candle_patterns["candle_analysis"]
                        patterns_message += f"*Thống kê:* {stats.get('total_special_candles', 0)} mẫu hình đặc biệt được phát hiện\n\n"
                    
                    # Hiển thị chi tiết các mẫu hình nếu có
                    if "highlighted_patterns" in result:
                        highlighted = result["highlighted_patterns"]
                        patterns_message += "*Mẫu hình nến đánh dấu:*\n"
                        
                        # Hiển thị các loại pattern được đánh dấu trên biểu đồ
                        for pattern_name, pattern_info in highlighted.items():
                            patterns_message += f"• {pattern_name}: {pattern_info['count']} lần xuất hiện\n"
                        
                        patterns_message += "\n"
                    
                    # Phân tích gaps nếu có
                    if "gap_analysis" in candle_patterns:
                        gaps = candle_patterns["gap_analysis"]
                        if gaps.get("total_gaps", 0) > 0:
                            patterns_message += f"*Gaps:* {gaps.get('total_gaps')} khoảng trống được phát hiện\n"
                            patterns_message += f"• Rising Windows (tín hiệu tăng): {gaps.get('rising_windows', 0)}\n"
                            patterns_message += f"• Falling Windows (tín hiệu giảm): {gaps.get('falling_windows', 0)}\n\n"
                    
                    await update.message.reply_text(
                        patterns_message,
                        parse_mode="Markdown"
                    )
                
                # 2. Phân tích Trend Analysis nếu TR được bật trong settings
                if "trend_analysis" in result and plot_settings.get("TR", False):
                    additional_info_sent = True
                    trend_message = "*📈 PHÂN TÍCH XU HƯỚNG:*\n\n"
                    
                    # Lấy thông tin từ API response
                    trend_data = result["trend_analysis"]
                    
                    # Hiển thị tóm tắt xu hướng
                    if "summary" in trend_data:
                        summary = trend_data["summary"]
                        total_periods = summary.get("total_periods", 0)
                        dominant_trend = summary.get("dominant_trend")
                        
                        # Biểu tượng xu hướng
                        trend_icon = "🟢" if dominant_trend == "uptrend" else "🔴" if dominant_trend == "downtrend" else "�"
                        
                        # Tên xu hướng tiếng Việt
                        trend_name_vi = "Tăng" if dominant_trend == "uptrend" else "Giảm" if dominant_trend == "downtrend" else "Đi ngang"
                        
                        trend_message += f"*Xu hướng chính:* {trend_icon} {trend_name_vi}\n"
                        trend_message += f"*Số chu kỳ phát hiện:* {total_periods}\n"
                        trend_message += f"• Chu kỳ tăng: {summary.get('uptrend_periods', 0)}\n"
                        trend_message += f"• Chu kỳ giảm: {summary.get('downtrend_periods', 0)}\n\n"
                    
                    # Hiển thị chi tiết các chu kỳ xu hướng (tối đa 5 chu kỳ gần nhất)
                    if "weekly_trends" in trend_data:
                        trends = trend_data["weekly_trends"]
                        recent_trends = trends[-5:] if len(trends) > 5 else trends
                        
                        if recent_trends:
                            trend_message += "*Các chu kỳ xu hướng gần đây:*\n"
                            
                            for trend in recent_trends:
                                trend_type = trend.get("trend")
                                period = trend.get("period")
                                percent_change = trend.get("percent_change")
                                days_count = trend.get("days_count")
                                
                                # Biểu tượng xu hướng
                                trend_icon = "🟢" if trend_type == "uptrend" else "🔴" if trend_type == "downtrend" else "🟡"
                                
                                trend_message += f"{trend_icon} *{period}* ({days_count} ngày): {percent_change}\n"
                    
                    await update.message.reply_text(
                        trend_message,
                        parse_mode="Markdown"
                    )
                
                # Nếu không có thông tin bổ sung nào được hiển thị nhưng CP hoặc TR được bật
                if not additional_info_sent and (plot_settings.get("CP", False) or plot_settings.get("TR", False)):
                    await update.message.reply_text(
                        "⚠️ Không có thông tin phân tích bổ sung nào được phát hiện cho mã này.",
                        parse_mode="Markdown"
                    )
            else:
                await update.message.reply_text("❌ Không thể tạo biểu đồ.")
        else:
            # Xóa thông báo đang xử lý
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=processing_message.message_id
            )
            
            error_message = f"❌ Lỗi: {response.status_code}"
            try:
                error_detail = response.json().get("detail", response.text)
                error_message += f"\n{error_detail}"
            except:
                error_message += f"\n{response.text}"
                
            await update.message.reply_text(error_message)
    
    except Exception as e:
        logger.error(f"Error in chart command: {str(e)}", exc_info=True)
        # Xóa thông báo đang xử lý
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=processing_message.message_id
            )
        except:
            pass
            
        await update.message.reply_text(
            f"❌ Không thể tạo biểu đồ: {str(e)}\n"
            f"Vui lòng kiểm tra lại kết nối hoặc thử lại sau."
        )

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tin nhắn không phải là lệnh"""
    text = update.message.text
    
    # Kiểm tra xem có phải là mã chứng khoán không (3-4 chữ cái viết hoa)
    if text.isupper() and 2 <= len(text) <= 4 and text.isalpha():
        # Người dùng có thể đã nhập mã chứng khoán
        keyboard = [
            [
                InlineKeyboardButton(f"Phân tích ngắn hạn {text}", callback_data=f"analyze_{text}_short"),
                InlineKeyboardButton(f"Phân tích dài hạn {text}", callback_data=f"analyze_{text}_long")
            ],
            [
                InlineKeyboardButton(f"Biểu đồ {text}", callback_data=f"chart_{text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Bạn muốn thực hiện hành động nào với mã *{text}*?",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        # Gửi hướng dẫn nếu không phải lệnh
        await update.message.reply_text(
            "Tôi không hiểu tin nhắn của bạn. Vui lòng sử dụng các lệnh:\n"
            "/predict [mã CK] [short/long] - Phân tích cổ phiếu\n"
            "/chart [mã CK] - Xem biểu đồ kỹ thuật\n"
            "/help - Xem hướng dẫn chi tiết"
        )

async def callback_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý hành động từ inline keyboard buttons"""
    query = update.callback_query
    await query.answer()
    
    # Xử lý các loại callback data
    if query.data.startswith("analyze_"):
        parts = query.data.split("_")
        symbol = parts[1]
        
        # Kiểm tra xem có tham số range không
        if len(parts) > 2:
            range_value = parts[2]  # short hoặc long
            context.args = [symbol, range_value]
        else:
            # Nếu không có tham số range, hiển thị thông báo lỗi
            await query.message.reply_text(
                "⚠️ Lỗi: Thiếu tham số khung thời gian (short/long).",
                parse_mode="Markdown"
            )
            return
            
        await predict(query, context)
    
    elif query.data.startswith("chart_"):
        symbol = query.data.split("_")[1]
        # Giả lập lệnh chart
        context.args = [symbol]
        await chart(query, context)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hàm xử lý khi người dùng sử dụng lệnh /settings"""
    # Hiển thị các nút để điều hướng đến các phần cài đặt khác nhau
    keyboard = [
        [InlineKeyboardButton("⚙️ Cài đặt biểu đồ", callback_data="settings_plot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛠️ *CÀI ĐẶT HỆ THỐNG*\n\n"
        "Vui lòng chọn phần cài đặt bạn muốn thay đổi:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý callback từ các nút cài đặt"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Xử lý hiển thị cài đặt biểu đồ
    if query.data == "settings_plot":
        # Lấy cài đặt hiện tại của người dùng
        plot_settings = get_plot_settings(user_id)
        
        # Tạo các nút toggle cho từng cài đặt
        keyboard = []
        
        # Các chỉ báo kỹ thuật chính
        indicators = [
            ("MA", "Moving Averages"),
            ("BB", "Bollinger Bands"),
            ("RSI", "RSI"),
            ("MACD", "MACD"),
            ("ICH", "Ichimoku"),
            ("SR", "Support & Resistance"),
            ("TR", "Trend Analysis"),
            ("CP", "Candle Patterns")
        ]
        
        # Thêm các nút chỉ báo chính
        for key, name in indicators:
            status = "✅ Bật" if plot_settings.get(key, False) else "❌ Tắt"
            keyboard.append([
                InlineKeyboardButton(f"{name}: {status}", callback_data=f"toggle_plot_{key}")
            ])
        
        # Thêm nút để mở rộng phần cài đặt mẫu hình nến
        keyboard.append([
            InlineKeyboardButton("📊 Cài đặt mẫu hình nến", callback_data="settings_candle_patterns")
        ])
        
        # Thêm nút quay lại và khôi phục mặc định
        keyboard.append([
            InlineKeyboardButton("↩️ Quay lại", callback_data="settings_back"),
            InlineKeyboardButton("🔄 Mặc định", callback_data="settings_plot_reset")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ *CÀI ĐẶT BIỂU ĐỒ*\n\n"
            "Chọn các chỉ báo kỹ thuật bạn muốn hiển thị trên biểu đồ.\n"
            "Cài đặt này sẽ được sử dụng khi bạn dùng lệnh `/chart`.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    # Xử lý hiển thị cài đặt mẫu hình nến
    elif query.data == "settings_candle_patterns":
        # Lấy cài đặt hiện tại của người dùng
        plot_settings = get_plot_settings(user_id)
        
        # Các mẫu hình nến
        patterns = [
            ("highlight_marubozu", "Marubozu"),
            ("highlight_spinning_top", "Spinning Top"),
            ("highlight_hammer", "Hammer"),
            ("highlight_hanging_man", "Hanging Man"),
            ("highlight_inverted_hammer", "Inverted Hammer"),
            ("highlight_shooting_star", "Shooting Star"),
            ("highlight_star_doji", "Star Doji"),
            ("highlight_long_legged_doji", "Long Legged Doji"),
            ("highlight_dragonfly_doji", "Dragonfly Doji"),
            ("highlight_gravestone_doji", "Gravestone Doji")
        ]
        
        # Tạo các nút toggle cho mẫu hình nến
        keyboard = []
        for key, name in patterns:
            status = "✅ Bật" if plot_settings.get(key, False) else "❌ Tắt"
            keyboard.append([
                InlineKeyboardButton(f"{name}: {status}", callback_data=f"toggle_plot_{key}")
            ])
        
        # Thêm nút quay lại
        keyboard.append([
            InlineKeyboardButton("↩️ Quay lại", callback_data="settings_plot")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🕯️ *CÀI ĐẶT MẪU HÌNH NẾN*\n\n"
            "Chọn các mẫu hình nến bạn muốn đánh dấu trên biểu đồ.\n"
            "Lưu ý: Cài đặt 'Candle Patterns' phải được bật để các đánh dấu này có hiệu lực.\n"
            "Chỉ được bật tối đa 4 loại nến cùng lúc",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    # Xử lý toggle cài đặt
    elif query.data.startswith("toggle_plot_"):
        setting_key = query.data.replace("toggle_plot_", "")
        
        # Lấy cài đặt hiện tại và toggle giá trị
        plot_settings = get_plot_settings(user_id)
        current_value = plot_settings.get(setting_key, False)
        #plot_settings[setting_key] = not current_value
        
        # # Lưu cài đặt mới
        # update_plot_settings(user_id, {setting_key: not current_value})
        
        if setting_key.startswith("highlight_") and not current_value:
    # Danh sách các key liên quan đến mẫu hình nến
            candle_pattern_keys = [
                "highlight_marubozu", "highlight_spinning_top", "highlight_hammer",
                "highlight_hanging_man", "highlight_inverted_hammer", "highlight_shooting_star",
                "highlight_star_doji", "highlight_long_legged_doji", 
                "highlight_dragonfly_doji", "highlight_gravestone_doji"
            ]
    
    # Đếm số mẫu hình nến đang được bật
            enabled_patterns = sum(1 for key in candle_pattern_keys if plot_settings.get(key, False))
    
    # Nếu đã có 4 mẫu hình được bật, không cho bật thêm
            if enabled_patterns >= 4:
                await query.answer("⚠️ Chỉ được bật tối đa 4 loại nến đặc biệt cùng lúc. Vui lòng tắt một loại trước khi bật loại này.")
                return
        
        # Nếu không vượt quá giới hạn hoặc đang tắt một cài đặt, thực hiện bình thường
        plot_settings[setting_key] = not current_value
        
        # Lưu cài đặt mới
        update_plot_settings(user_id, {setting_key: not current_value})

        # Hiển thị thông báo thành công và cập nhật menu
        if setting_key.startswith("highlight_"):
            await query.answer(f"Đã {'bật' if not current_value else 'tắt'} {setting_key.replace('highlight_', '')}")
            # Tạo lại menu cài đặt mẫu hình nến
            # Lấy cài đặt hiện tại của người dùng
            plot_settings = get_plot_settings(user_id)
            
            # Các mẫu hình nến
            patterns = [
                ("highlight_marubozu", "Marubozu"),
                ("highlight_spinning_top", "Spinning Top"),
                ("highlight_hammer", "Hammer"),
                ("highlight_hanging_man", "Hanging Man"),
                ("highlight_inverted_hammer", "Inverted Hammer"),
                ("highlight_shooting_star", "Shooting Star"),
                ("highlight_star_doji", "Star Doji"),
                ("highlight_long_legged_doji", "Long Legged Doji"),
                ("highlight_dragonfly_doji", "Dragonfly Doji"),
                ("highlight_gravestone_doji", "Gravestone Doji")
            ]
            
            # Tạo các nút toggle cho mẫu hình nến
            keyboard = []
            for key, name in patterns:
                status = "✅ Bật" if plot_settings.get(key, False) else "❌ Tắt"
                keyboard.append([
                    InlineKeyboardButton(f"{name}: {status}", callback_data=f"toggle_plot_{key}")
                ])
            
            # Thêm nút quay lại
            keyboard.append([
                InlineKeyboardButton("↩️ Quay lại", callback_data="settings_plot")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🕯️ *CÀI ĐẶT MẪU HÌNH NẾN*\n\n"
                "Chọn các mẫu hình nến bạn muốn đánh dấu trên biểu đồ.\n"
                "Lưu ý: Cài đặt 'Candle Patterns' phải được bật để các đánh dấu này có hiệu lực.\n"
                "Chỉ được phép hiển thị tối đa 4 loại nến cùng lúc. Vui lòng tắt một loại nến khác trước.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await query.answer(f"Đã {'bật' if not current_value else 'tắt'} {setting_key}")
            # Tạo lại menu cài đặt chính
            # Lấy cài đặt hiện tại của người dùng
            plot_settings = get_plot_settings(user_id)
            
            # Tạo các nút toggle cho từng cài đặt
            keyboard = []
            
            # Các chỉ báo kỹ thuật chính
            indicators = [
                ("MA", "Moving Averages"),
                ("BB", "Bollinger Bands"),
                ("RSI", "RSI"),
                ("MACD", "MACD"),
                ("ICH", "Ichimoku"),
                ("SR", "Support & Resistance"),
                ("TR", "Trend Analysis"),
                ("CP", "Candle Patterns")
            ]
            
            # Thêm các nút chỉ báo chính
            for key, name in indicators:
                status = "✅ Bật" if plot_settings.get(key, False) else "❌ Tắt"
                keyboard.append([
                    InlineKeyboardButton(f"{name}: {status}", callback_data=f"toggle_plot_{key}")
                ])
            
            # Thêm nút để mở rộng phần cài đặt mẫu hình nến
            keyboard.append([
                InlineKeyboardButton("📊 Cài đặt mẫu hình nến", callback_data="settings_candle_patterns")
            ])
            
            # Thêm nút quay lại và khôi phục mặc định
            keyboard.append([
                InlineKeyboardButton("↩️ Quay lại", callback_data="settings_back"),
                InlineKeyboardButton("🔄 Mặc định", callback_data="settings_plot_reset")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚙️ *CÀI ĐẶT BIỂU ĐỒ*\n\n"
                "Chọn các chỉ báo kỹ thuật bạn muốn hiển thị trên biểu đồ.\n"
                "Cài đặt này sẽ được sử dụng khi bạn dùng lệnh `/chart`.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        return
    
    # Xử lý khôi phục cài đặt mặc định
    elif query.data == "settings_plot_reset":
        # Khôi phục tất cả cài đặt về mặc định
        update_plot_settings(user_id, DEFAULT_PLOT_SETTINGS)
        
        await query.answer("Đã khôi phục cài đặt biểu đồ về mặc định")
        
        # Tạo lại menu cài đặt chính với các giá trị mặc định
        plot_settings = get_plot_settings(user_id)
            
        # Tạo các nút toggle cho từng cài đặt
        keyboard = []
        
        # Các chỉ báo kỹ thuật chính
        indicators = [
            ("MA", "Moving Averages"),
            ("BB", "Bollinger Bands"),
            ("RSI", "RSI"),
            ("MACD", "MACD"),
            ("ICH", "Ichimoku"),
            ("SR", "Support & Resistance"),
            ("TR", "Trend Analysis"),
            ("CP", "Candle Patterns")
        ]
        
        # Thêm các nút chỉ báo chính
        for key, name in indicators:
            status = "✅ Bật" if plot_settings.get(key, False) else "❌ Tắt"
            keyboard.append([
                InlineKeyboardButton(f"{name}: {status}", callback_data=f"toggle_plot_{key}")
            ])
        
        # Thêm nút để mở rộng phần cài đặt mẫu hình nến
        keyboard.append([
            InlineKeyboardButton("📊 Cài đặt mẫu hình nến", callback_data="settings_candle_patterns")
        ])
        
        # Thêm nút quay lại và khôi phục mặc định
        keyboard.append([
            InlineKeyboardButton("↩️ Quay lại", callback_data="settings_back"),
            InlineKeyboardButton("🔄 Mặc định", callback_data="settings_plot_reset")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ *CÀI ĐẶT BIỂU ĐỒ*\n\n"
            "Chọn các chỉ báo kỹ thuật bạn muốn hiển thị trên biểu đồ.\n"
            "Cài đặt này sẽ được sử dụng khi bạn dùng lệnh `/chart`.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return
    
    # Xử lý quay lại
    elif query.data == "settings_back":
        await settings_command(query, context)

def main() -> None:
    """Hàm chính để khởi chạy bot"""
    # Khởi tạo bot với token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN không được định nghĩa trong file .env")
        return
        
    app = ApplicationBuilder().token(token).build()
    
    # Đăng ký các handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("settings", settings_command))
    
    # Callback handlers cho các inline buttons
    app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^help_"))
    app.add_handler(CallbackQueryHandler(callback_actions, pattern=r"^(analyze_|chart_)"))
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern=r"^(settings_|toggle_plot_)"))
    
    # Handler cho các tin nhắn không phải lệnh
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))
    
    # Bắt đầu bot
    logger.info("Bot đang chạy...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()