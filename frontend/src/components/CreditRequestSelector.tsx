import React, { useState, useEffect } from 'react';

interface CreditRequest {
	request_id: string;
	borrower_name: string;
	loan_amount: number;
	status: string;
}

interface CreditRequestSelectorProps {
	onSelectRequest: (requestId: string) => void;
}

const CreditRequestSelector: React.FC<CreditRequestSelectorProps> = ({
	onSelectRequest,
}) => {
	const [creditRequests, setCreditRequests] = useState<CreditRequest[]>([]);
	const [selectedRequestId, setSelectedRequestId] = useState<string>('');
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// Fetch credit requests on component mount
	useEffect(() => {
		fetchCreditRequests();
	}, []);

	const fetchCreditRequests = async () => {
		setIsLoading(true);
		setError(null);
		try {
			const response = await fetch('http://localhost:8000/credit-requests');
			if (!response.ok) {
				throw new Error('Failed to fetch credit requests');
			}
			const data = await response.json();
			setCreditRequests(data);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'An error occurred');
		} finally {
			setIsLoading(false);
		}
	};

	const handleSelectRequest = (requestId: string) => {
		setSelectedRequestId(requestId);
		onSelectRequest(requestId);
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case 'pending':
				return 'bg-yellow-100 text-yellow-800';
			case 'under_review':
				return 'bg-blue-100 text-blue-800';
			case 'approved':
				return 'bg-green-100 text-green-800';
			case 'rejected':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	};

	const formatAmount = (amount: number) => {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0,
		}).format(amount);
	};

	return (
		<div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4'>
			<div className='flex items-center justify-between mb-3'>
				<h3 className='text-lg font-semibold text-gray-800'>
					Credit Requests
				</h3>
				<button
					onClick={fetchCreditRequests}
					disabled={isLoading}
					className='text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50'>
					{isLoading ? (
						<div className='flex items-center space-x-1'>
							<div className='w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin'></div>
							<span>Loading...</span>
						</div>
					) : (
						'Refresh'
					)}
				</button>
			</div>

			{error && (
				<div className='mb-3 p-3 bg-red-50 border border-red-200 rounded-md'>
					<p className='text-sm text-red-600'>{error}</p>
				</div>
			)}

			{creditRequests.length === 0 && !isLoading && !error && (
				<div className='text-center py-4 text-gray-500'>
					No credit requests found
				</div>
			)}

			{creditRequests.length > 0 && (
				<div className='space-y-2'>
					<select
						value={selectedRequestId}
						onChange={(e) => handleSelectRequest(e.target.value)}
						className='w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent'>
						<option value=''>Select a credit request...</option>
						{creditRequests.map((request) => (
							<option key={request.request_id} value={request.request_id}>
								{request.request_id} - {request.borrower_name} (
								{formatAmount(request.loan_amount)})
							</option>
						))}
					</select>

					{selectedRequestId && (
						<div className='mt-3 p-3 bg-gray-50 rounded-md'>
							{creditRequests
								.filter((req) => req.request_id === selectedRequestId)
								.map((request) => (
									<div key={request.request_id} className='space-y-2'>
										<div className='flex justify-between items-start'>
											<div>
												<p className='text-sm font-medium text-gray-800'>
													{request.borrower_name}
												</p>
												<p className='text-xs text-gray-600'>
													Request ID: {request.request_id}
												</p>
												<p className='text-sm text-gray-700'>
													Loan Amount: {formatAmount(request.loan_amount)}
												</p>
											</div>
											<span
												className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
													request.status
												)}`}>
												{request.status.replace('_', ' ')}
											</span>
										</div>
									</div>
								))}
						</div>
					)}
				</div>
			)}
		</div>
	);
};

export default CreditRequestSelector;