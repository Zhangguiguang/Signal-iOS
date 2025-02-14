//
//  Copyright (c) 2021 Open Whisper Systems. All rights reserved.
//

import Foundation

// Outgoing message approval can be a multi-step process.
@objc
public enum ApprovalMode: UInt {
    // This is the final step of approval; continuing will send.
    case send
    // This is not the final step of approval; continuing will not send.
    case next
    // This step is not yet ready to proceed.
    case loading
}

// MARK: -

public protocol ApprovalFooterDelegate: AnyObject {
    func approvalFooterDelegateDidRequestProceed(_ approvalFooterView: ApprovalFooterView)

    func approvalMode(_ approvalFooterView: ApprovalFooterView) -> ApprovalMode

    var approvalFooterHasTextInput: Bool { get }

    var approvalFooterTextInputDefaultText: String? { get }

    func approvalFooterDidBeginEditingText()
}

// MARK: -

public class ApprovalFooterView: UIView {
    public weak var delegate: ApprovalFooterDelegate? {
        didSet {
            updateContents()
        }
    }

    private let backgroundView = UIView()
    private let topStrokeView = UIView()

    public var textInput: String? {
        textfield.text
    }

    private var approvalMode: ApprovalMode {
        guard let delegate = delegate else {
            return .send
        }
        return delegate.approvalMode(self)
    }

    override init(frame: CGRect) {
        super.init(frame: frame)

        autoresizingMask = .flexibleHeight
        translatesAutoresizingMaskIntoConstraints = false

        layoutMargins = UIEdgeInsets(top: 10, left: 16, bottom: 10, right: 16)

        // We extend our background view below the keyboard to avoid any gaps.
        addSubview(backgroundView)
        backgroundView.autoPinWidthToSuperview()
        backgroundView.autoPinEdge(toSuperviewEdge: .top)
        backgroundView.autoPinEdge(toSuperviewEdge: .bottom, withInset: -30)

        addSubview(topStrokeView)
        topStrokeView.autoPinEdgesToSuperviewEdges(with: .zero, excludingEdge: .bottom)
        topStrokeView.autoSetDimension(.height, toSize: CGHairlineWidth())

        let hStackView = UIStackView(arrangedSubviews: [labelScrollView, proceedButton])
        hStackView.axis = .horizontal
        hStackView.spacing = 12
        hStackView.alignment = .center

        let vStackView = UIStackView(arrangedSubviews: [textfieldStack, hStackView])
        vStackView.axis = .vertical
        vStackView.spacing = 16
        vStackView.alignment = .fill
        addSubview(vStackView)
        vStackView.autoPinEdgesToSuperviewMargins()

        updateContents()

        let textfieldBackgroundView = textfieldStack.addBackgroundView(withBackgroundColor: Theme.backgroundColor)
        textfieldBackgroundView.layer.cornerRadius = 10
        self.textfieldBackgroundView = textfieldBackgroundView

        NotificationCenter.default.addObserver(self, selector: #selector(applyTheme), name: .ThemeDidChange, object: nil)
        applyTheme()
    }

    private var textfieldBackgroundView: UIView?

    @objc
    private func applyTheme() {
        backgroundView.backgroundColor = Theme.keyboardBackgroundColor
        topStrokeView.backgroundColor = Theme.hairlineColor
        namesLabel.textColor = Theme.secondaryTextAndIconColor
        textfield.textColor = Theme.secondaryTextAndIconColor
        textfieldBackgroundView?.backgroundColor = Theme.backgroundColor
    }

    required init?(coder aDecoder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    public override var intrinsicContentSize: CGSize {
        return CGSize.zero
    }

    // MARK: public

    private var namesText: String? {
        get {
            return namesLabel.text
        }
    }

    public func setNamesText(_ newValue: String?, animated: Bool) {
        let changes = {
            self.namesLabel.text = newValue

            self.layoutIfNeeded()

            let offset = max(0, self.labelScrollView.contentSize.width - self.labelScrollView.bounds.width)
            let trailingEdge = CGPoint(x: offset, y: 0)

            self.labelScrollView.setContentOffset(trailingEdge, animated: false)
        }

        if animated {
            UIView.animate(withDuration: 0.1, animations: changes)
        } else {
            changes()
        }
    }

    // MARK: private subviews

    lazy var labelScrollView: UIScrollView = {
        let scrollView = UIScrollView()
        scrollView.showsHorizontalScrollIndicator = false

        scrollView.addSubview(namesLabel)
        namesLabel.autoPinEdgesToSuperviewEdges()
        namesLabel.autoMatch(.height, to: .height, of: scrollView)

        return scrollView
    }()

    lazy var namesLabel: UILabel = {
        let label = UILabel()
        label.font = UIFont.ows_dynamicTypeBody

        label.setContentHuggingLow()

        return label
    }()

    lazy var textfield: UITextField = {
        let textfield = UITextField()
        textfield.font = UIFont.ows_dynamicTypeBody
        return textfield
    }()

    lazy var textfieldStack: UIStackView = {
        let textfieldStack = UIStackView(arrangedSubviews: [textfield])
        textfieldStack.axis = .vertical
        textfieldStack.alignment = .fill
        textfieldStack.layoutMargins = UIEdgeInsets(hMargin: 8, vMargin: 7)
        textfieldStack.isLayoutMarginsRelativeArrangement = true
        return textfieldStack
    }()

    var proceedLoadingIndicator = UIActivityIndicatorView(style: .white)
    lazy var proceedButton: OWSButton = {
		let button = OWSButton.sendButton(
			imageName: self.approvalMode.proceedButtonImageName ?? "arrow-right-24"
		) { [weak self] in
            guard let self = self else { return }
            self.delegate?.approvalFooterDelegateDidRequestProceed(self)
        }

        button.addSubview(proceedLoadingIndicator)
        proceedLoadingIndicator.autoCenterInSuperview()
        proceedLoadingIndicator.isHidden = true

        return button
    }()

    private var textfieldHeightConstraint: NSLayoutConstraint?

    func updateContents() {
        proceedButton.setImage(imageName: approvalMode.proceedButtonImageName)
        proceedButton.accessibilityLabel = approvalMode.proceedButtonAccessibilityLabel

        let hasTextInput = delegate?.approvalFooterHasTextInput ?? false
        textfieldStack.isHidden = !hasTextInput
        textfield.placeholder = delegate?.approvalFooterTextInputDefaultText
        textfield.delegate = self
        let textfieldHeight = textfield.intrinsicContentSize.height
        if let textfieldHeightConstraint = self.textfieldHeightConstraint {
            textfieldHeightConstraint.constant = textfieldHeight
        } else {
            textfieldHeightConstraint = textfield.autoSetDimension(.height, toSize: textfieldHeight)
        }

        if approvalMode == .loading {
            proceedLoadingIndicator.isHidden = false
            proceedLoadingIndicator.startAnimating()
        } else {
            proceedLoadingIndicator.stopAnimating()
            proceedLoadingIndicator.isHidden = true
        }
    }
}

// MARK: -

fileprivate extension ApprovalMode {
	var proceedButtonAccessibilityLabel: String? {
		switch self {
		case .next: return CommonStrings.nextButton
		case .send: return MessageStrings.sendButton
        case .loading: return nil
		}
	}

	var proceedButtonImageName: String? {
		switch self {
		case .next:
			return "arrow-right-24"
		case .send:
			return "send-solid-24"
        case .loading:
            return nil
		}
	}
}

// MARK: -

extension ApprovalFooterView: UITextFieldDelegate {
    public func textFieldDidBeginEditing(_ textField: UITextField) {
        delegate?.approvalFooterDidBeginEditingText()
    }

    public func textField(_ textField: UITextField, shouldChangeCharactersIn range: NSRange, replacementString string: String) -> Bool {
        return true
    }
}
